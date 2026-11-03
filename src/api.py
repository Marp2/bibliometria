"""API Flask de la aplicacion de bibliometria (analisis de algoritmos).

Paginas:  /ui/corpus  /ui/similarity  /ui/clustering  /ui/patterns  /ui/docs
JSON:     /health, /api/algorithm-docs, /api/corpus..., /api/similarity, /api/clustering..., /api/patterns...
Graficas: /plot/*.png      Informe: /report/<md|docx|pdf>
"""
import logging

from flask import Flask, Response, jsonify, redirect, request, send_file, send_from_directory

from src import clustering as cl
from src import visualizacion as vz
from src.benchmark_patrones import medir, medir_casos_sinteticos, medir_escalabilidad, texto_del_corpus
from src.comparacion import ErrorComparacion, algoritmos_disponibles, comparar, detalle_par
from src.corpus import ErrorCorpus, obtener_corpus
from src.docs_algoritmos import DOCS_ALGORITMOS
from src.patrones import ALGORITMOS, ErrorPatron, buscar_en_corpus, comparar_algoritmos, ejecutar
from src.paths import DOCS_DIR, STATIC_DIR, find_data_file
from src.preprocesamiento import preprocesar

MODULOS = ("corpus", "similarity", "clustering", "patterns", "docs")
MAX_CACHE = 64
MAX_TEXTO = 20000
_CACHE = {}

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("werkzeug").setLevel(logging.WARNING)


def _error(mensaje, codigo=400):
    r = jsonify({"detail": mensaje})
    r.status_code = codigo
    return r


def _cache(clave, funcion):
    if clave in _CACHE:
        return _CACHE[clave]
    valor = funcion()
    if len(_CACHE) >= MAX_CACHE:
        del _CACHE[next(iter(_CACHE))]
    _CACHE[clave] = valor
    return valor


@app.errorhandler(ErrorCorpus)
def _h_corpus(e):
    return _error(str(e), 404)


@app.errorhandler(ErrorComparacion)
def _h_comp(e):
    return _error(str(e), 400)


@app.errorhandler(ErrorPatron)
def _h_pat(e):
    return _error(str(e), 400)


@app.errorhandler(404)
def _h_404(e):
    return _error("Recurso no encontrado.", 404)


@app.errorhandler(Exception)
def _h_500(e):
    logging.exception("Error no controlado")
    return _error("Error interno del servidor.", 500)


def _c():
    return obtener_corpus()


def _etiquetas(corpus):
    return ["#%d" % d["id"] for d in corpus.documentos]


def _png(datos):
    return Response(datos, mimetype="image/png", headers={"Cache-Control": "public, max-age=300"})


def _bool(valor, defecto):
    if valor is None:
        return defecto
    return valor.lower() in ("1", "true", "si", "on", "yes")


# --------------------------------------------------------------------------- paginas
@app.get("/")
def raiz():
    return redirect("/ui/corpus")


@app.get("/ui/<modulo>")
def pagina(modulo):
    if modulo not in MODULOS:
        return _error("Modulo inexistente.", 404)
    return send_from_directory(str(STATIC_DIR / "modules" / modulo), "index.html")


@app.get("/health")
def health():
    try:
        corpus = _c()
        return jsonify({"status": "ok", "articulos": len(corpus.documentos),
                        "terminos_vocabulario": len(corpus.vocab["terminos"]), "modelos_embeddings": list(corpus.modelos)})
    except ErrorCorpus as e:
        return jsonify({"status": "error", "detail": str(e)}), 503


@app.get("/api/algorithm-docs")
def algorithm_docs():
    return jsonify(DOCS_ALGORITMOS)


# --------------------------------------------------------------------------- corpus
@app.get("/api/corpus")
def api_corpus():
    return jsonify(_c().resumen())


@app.get("/api/corpus/calidad")
def api_calidad():
    import json
    ruta = find_data_file("reporte_calidad.json")
    if ruta is None:
        return _error("No existe reporte_calidad.json (ejecute scripts/extraer_corpus.py).", 404)
    with open(str(ruta), encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.get("/api/corpus/<int:id_doc>")
def api_doc(id_doc):
    d = _c().obtener(id_doc)
    pre = d["pre"]
    return jsonify({"id": d["id"], "titulo": d["titulo"], "autores": d["autores"], "abstract": d["abstract"],
                    "preprocesamiento": {k: pre[k] for k in ("minusculas", "sin_signos", "tokens", "tokens_sin_stopwords",
                                                              "tokens_finales", "texto_limpio")}})


@app.post("/api/preprocesar")
def api_preprocesar():
    datos = request.get_json(silent=True) or {}
    texto = datos.get("texto", "")
    if not isinstance(texto, str) or texto.strip() == "":
        return _error("Escriba un texto para preprocesar.")
    if len(texto) > MAX_TEXTO:
        return _error("El texto supera %d caracteres." % MAX_TEXTO)
    pre = preprocesar(texto, bool(datos.get("stemming", True)))
    return jsonify({k: pre[k] for k in ("minusculas", "sin_tildes", "sin_signos", "tokens", "tokens_sin_stopwords",
                                         "tokens_finales")})


# --------------------------------------------------------------------------- requerimiento 1
@app.post("/api/similarity")
def api_similarity():
    datos = request.get_json(silent=True) or {}
    ids = datos.get("ids")
    corpus = _c()
    return jsonify(comparar(corpus, ids))


@app.get("/api/similarity/detalle")
def api_similarity_detalle():
    try:
        a, b = int(request.args.get("a", "")), int(request.args.get("b", ""))
    except ValueError:
        return _error("Parametros 'a' y 'b' invalidos.")
    if a == b:
        return _error("Seleccione dos articulos distintos.")
    return jsonify(_cache(("detalle", a, b), lambda: detalle_par(_c(), a, b)))


@app.get("/api/similarity/algoritmos")
def api_sim_algs():
    return jsonify(algoritmos_disponibles(_c()))


@app.get("/plot/similarity.png")
def plot_similarity():
    corpus = _c()
    ids = [int(x) for x in request.args.get("ids", "").split(",") if x.strip().isdigit()]
    alg = request.args.get("algoritmo", "tfidf-coseno")

    def construir():
        r = comparar(corpus, ids)
        if alg not in r["matrices"]:
            raise ErrorComparacion("Algoritmo desconocido: %s" % alg)
        nombre = [a["nombre"] for a in r["algoritmos"] if a["clave"] == alg][0]
        return vz.png_heatmap(r["matrices"][alg], ["#%d" % i for i in r["ids"]], "Similitud: " + nombre)
    return _png(_cache(("hm", tuple(ids), alg), construir))


# --------------------------------------------------------------------------- requerimiento 2
def _evaluacion():
    def construir():
        corpus = _c()
        D = cl.matriz_distancias([d["tfidf"] for d in corpus.documentos])
        return D, cl.comparar_criterios(D)
    return _cache(("clustering",), construir)


@app.get("/api/clustering/comparar")
def api_clustering_comparar():
    D, comp = _evaluacion()
    corpus = _c()
    return jsonify({"documentos": [{"id": d["id"], "titulo": d["titulo"]} for d in corpus.documentos],
                    "mejor": comp["mejor"], "ranking": comp["ranking"],
                    "criterios": [{"criterio": r["criterio"], "nombre": r["nombre"], "ccc": r["ccc"],
                                   "mejor_k": r["mejor_k"], "mejor_silueta": r["mejor_silueta"],
                                   "siluetas": r["siluetas"], "historial": r["historial"]} for r in comp["resultados"]]})


@app.get("/api/clustering/matriz")
def api_clustering_matriz():
    D, _ = _evaluacion()
    return jsonify({"ids": _c().ids(), "distancias": D})


@app.get("/api/clustering/grupos")
def api_clustering_grupos():
    criterio = request.args.get("criterio", "average")
    if criterio not in cl.CRITERIOS:
        return _error("Criterio invalido (single, complete o average).")
    try:
        k = int(request.args.get("k", "3"))
    except ValueError:
        return _error("k invalido.")
    D, comp = _evaluacion()
    corpus = _c()
    if k < 2 or k > len(D):
        return _error("k debe estar entre 2 y %d." % len(D))
    r = [x for x in comp["resultados"] if x["criterio"] == criterio][0]
    etiquetas = cl.cortar_en_k(r["historial"], len(D), k)
    grupos = {}
    for pos, g in enumerate(etiquetas):
        grupos.setdefault(g, []).append({"id": corpus.documentos[pos]["id"], "titulo": corpus.documentos[pos]["titulo"]})
    return jsonify({"criterio": criterio, "k": k, "silueta": cl.silueta(D, etiquetas),
                    "grupos": [grupos[g] for g in sorted(grupos)]})


@app.get("/plot/dendrogram.png")
def plot_dendrogram():
    criterio = request.args.get("criterio", "average")
    if criterio not in cl.CRITERIOS:
        return _error("Criterio invalido (single, complete o average).")
    try:
        k = int(request.args.get("k", "0"))
    except ValueError:
        return _error("k invalido.")
    D, comp = _evaluacion()
    r = [x for x in comp["resultados"] if x["criterio"] == criterio][0]
    kk = k if 2 <= k <= len(D) else None
    return _png(_cache(("dendro", criterio, kk), lambda: vz.png_dendrograma(
        r["historial"], len(D), _etiquetas(_c()), criterio, r["ccc"], kk)))


@app.get("/plot/clustering_metricas.png")
def plot_clustering_metricas():
    _, comp = _evaluacion()
    return _png(_cache(("clmet",), lambda: vz.png_metricas_clustering(comp["resultados"])))


# --------------------------------------------------------------------------- requerimiento 3
def _patron_arg():
    patron = request.args.get("patron", "")
    if patron.strip() == "":
        raise ErrorPatron("Escriba un patron de busqueda.")
    return patron


@app.get("/api/patterns/search")
def api_patterns_search():
    patron = _patron_arg()
    algoritmo = request.args.get("algoritmo", "kmp")
    mayus = not _bool(request.args.get("distinguir_mayusculas"), False)
    corpus = _c()
    if algoritmo == "todos":
        comp = comparar_algoritmos(corpus.documentos, patron, mayus)
        base = buscar_en_corpus(corpus.documentos, patron, "kmp", mayus)
        base["comparacion"] = {"coinciden": comp["coinciden"],
                               "algoritmos": {a: {k: v for k, v in comp["algoritmos"][a].items() if k != "posiciones"}
                                              for a in comp["algoritmos"]}}
        base["algoritmo"] = "todos"
        return jsonify(base)
    if algoritmo not in ALGORITMOS:
        raise ErrorPatron("Algoritmo desconocido: %s" % algoritmo)
    return jsonify(buscar_en_corpus(corpus.documentos, patron, algoritmo, mayus))


@app.get("/api/patterns/benchmark")
def api_patterns_benchmark():
    patron = _patron_arg()
    try:
        reps = int(request.args.get("repeticiones", "5"))
    except ValueError:
        return _error("repeticiones invalido.")
    reps = max(1, min(reps, 15))
    texto = texto_del_corpus(_c().documentos)
    return jsonify(_cache(("bench", patron, reps), lambda: {
        "n": len(texto), "patron": patron, "m": len(patron), "repeticiones": reps,
        "corpus": medir(texto, patron, reps),
        "escalabilidad": medir_escalabilidad(texto, patron, (1, 2, 4, 8), max(1, reps // 2)),
        "sinteticos": medir_casos_sinteticos(8000, 30, 2)}))


@app.get("/api/patterns/traza")
def api_patterns_traza():
    patron = _patron_arg()
    algoritmo = request.args.get("algoritmo", "kmp")
    if algoritmo not in ALGORITMOS:
        raise ErrorPatron("Algoritmo desconocido: %s" % algoritmo)
    d = _c().obtener(request.args.get("doc", ""))
    r = ejecutar(algoritmo, d["abstract"], patron, not _bool(request.args.get("distinguir_mayusculas"), False), True)
    return jsonify({"id": d["id"], "posiciones": r["posiciones"], "comparaciones": r["comparaciones"],
                    "extras": r["extras"], "iteraciones": len(r["traza"]), "traza": r["traza"][:300]})


@app.get("/plot/patterns.png")
def plot_patterns():
    patron = _patron_arg()
    algoritmo = request.args.get("algoritmo", "kmp")
    if algoritmo not in ALGORITMOS:
        raise ErrorPatron("Algoritmo desconocido: %s" % algoritmo)
    d = _c().obtener(request.args.get("doc", ""))
    mayus = not _bool(request.args.get("distinguir_mayusculas"), False)
    defecto = {"kmp": 160, "boyer-moore": 200, "rabin-karp": 70}[algoritmo]
    try:
        largo = max(len(patron) + 1, min(int(request.args.get("largo", str(defecto))), 300))
        if request.args.get("desde") is not None:
            ini = max(0, int(request.args.get("desde")))
        else:
            # por defecto, centrar el fragmento en la primera ocurrencia (si existe)
            primera = ejecutar(algoritmo, d["abstract"], patron, mayus)["posiciones"]
            ini = max(0, primera[0] - 20) if len(primera) > 0 else 0
    except ValueError:
        return _error("Parametros 'desde' y 'largo' invalidos.")
    fragmento = d["abstract"][ini:ini + largo]
    r = ejecutar(algoritmo, fragmento, patron, mayus, True)
    return _png(vz.png_alineaciones(fragmento, patron, algoritmo, r["traza"]))


# --------------------------------------------------------------------------- informe
@app.get("/report/<formato>")
def informe(formato):
    nombres = {"md": "DOCUMENTO_TECNICO_FINAL.md", "docx": "DOCUMENTO_TECNICO_FINAL.docx", "pdf": "DOCUMENTO_TECNICO_FINAL.pdf",
               "guia": "GUIA_SUSTENTACION_PROYECTO.md"}
    if formato not in nombres:
        return _error("Formato invalido (md, docx, pdf o guia).", 404)
    ruta = DOCS_DIR / nombres[formato]
    if not ruta.exists():
        return _error("El archivo todavia no existe en el servidor.", 404)
    return send_file(str(ruta), as_attachment=True, download_name=nombres[formato])
