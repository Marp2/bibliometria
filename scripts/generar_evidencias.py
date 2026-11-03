"""Ejecuta los algoritmos REALES sobre el corpus y guarda todas las evidencias de la documentacion.

Salidas:
  docs/evidencias/evidencias.json   numeros, tablas y trazas usados por scripts/generar_documentos.py
  docs/figuras/*.png                dendrogramas, mapas de calor, iteraciones de los algoritmos, tiempos

Uso:  python scripts/generar_evidencias.py        (tarda ~1-2 minutos: mide tiempos reales)
Ningun numero de los documentos se escribe a mano: todos salen de este script.
"""
import json
import os
import platform
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from src import clustering as cl  # noqa: E402
from src import visualizacion as vz  # noqa: E402
from src.benchmark_patrones import medir, medir_casos_sinteticos, medir_escalabilidad, texto_del_corpus  # noqa: E402
from src.comparacion import detalle_par, similitud_par  # noqa: E402
from src.corpus import obtener_corpus  # noqa: E402
from src.estructuras_datos import mediana, ordenar_por_mezcla, promedio  # noqa: E402
from src.patrones import (ALGORITMOS, bm_preprocesar, ejecutar, kmp_tabla_lps, rk_buscar, rk_hash,  # noqa: E402
                          rk_preprocesar)
from src.preprocesamiento import preprocesar  # noqa: E402
from src.similitud_clasica import (levenshtein_distancia, levenshtein_matriz, needleman_wunsch_alineamiento,  # noqa: E402
                                   needleman_wunsch_normalizado, needleman_wunsch_puntaje)
from src.similitud_embeddings import coseno, distancia_euclidiana  # noqa: E402

FIG = os.path.join(RAIZ, "docs", "figuras")
EVI = os.path.join(RAIZ, "docs", "evidencias")
os.makedirs(FIG, exist_ok=True)
os.makedirs(EVI, exist_ok=True)

CASO_A, CASO_B = 2, 6            # par MAS similar segun coseno TF-IDF entre los 190 pares (criterio objetivo)
CONTRASTE_A, CONTRASTE_B = 14, 19  # par MENOS similar segun coseno TF-IDF
PATRON = "perspectives"           # tabla LPS no trivial y aparece en el corpus
DOC_PATRON = 9
CLAVES = ("levenshtein", "needleman-wunsch", "tfidf-coseno", "jaccard", "emb-glove", "emb-fasttext")


def guardar_png(nombre, datos):
    with open(os.path.join(FIG, nombre), "wb") as f:
        f.write(datos)


def rangos(valores):
    """Rangos con promedio en empates (para Spearman)."""
    orden = ordenar_por_mezcla(list(range(len(valores))), clave=lambda i: valores[i])
    r = [0.0] * len(valores)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and valores[orden[j + 1]] == valores[orden[i]]:
            j += 1
        prom = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[orden[k]] = prom
        i = j + 1
    return r


def spearman(x, y):
    return cl.pearson(rangos(x), rangos(y))


def main():
    t_inicio = time.time()
    corpus = obtener_corpus()
    docs = corpus.documentos
    ev = {"maquina": {"python": platform.python_version(), "sistema": platform.platform(), "cpus": os.cpu_count()}}

    # ------------------------------------------------------------------ corpus / preprocesamiento
    sin_stem = [preprocesar(d["abstract"], False) for d in docs]
    con_stem = [d["pre"] for d in docs]
    vocab_sin, vocab_con = {}, {}
    for p in sin_stem:
        for t in p["tokens_finales"]:
            vocab_sin[t] = 1
    for p in con_stem:
        for t in p["tokens_finales"]:
            vocab_con[t] = 1
    ev["corpus"] = {
        "articulos": [{"id": d["id"], "titulo": d["titulo"], "autores": d["autores"], "palabras": len(d["pre"]["tokens"]),
                       "caracteres": len(d["abstract"]), "tokens_utiles": len(d["pre"]["tokens_sin_stopwords"])} for d in docs],
        "tokens_totales": sum(len(d["pre"]["tokens"]) for d in docs),
        "tokens_utiles": sum(len(d["pre"]["tokens_sin_stopwords"]) for d in docs),
        "vocab_sin_stemming": len(vocab_sin), "vocab_con_stemming": len(vocab_con),
    }
    with open(os.path.join(RAIZ, "data", "processed", "reporte_calidad.json"), encoding="utf-8") as f:
        ev["calidad"] = json.load(f)
    limpio = [{"id": d["id"], "titulo": d["titulo"], "texto_normalizado": d["pre"]["texto_normalizado"],
               "texto_limpio": d["pre"]["texto_limpio"], "tokens_finales": d["pre"]["tokens_finales"]} for d in docs]
    with open(os.path.join(RAIZ, "data", "processed", "corpus_limpio.json"), "w", encoding="utf-8") as f:
        json.dump(limpio, f, ensure_ascii=False, indent=1)

    # ------------------------------------------------------------------ requerimiento 1: todos los pares
    pares = []
    tiempos = {k: [] for k in CLAVES}
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            r = similitud_par(corpus, docs[i], docs[j])
            pares.append({"a": docs[i]["id"], "b": docs[j]["id"], "s": {k: r[k]["similitud"] for k in CLAVES}})
            for k in CLAVES:
                tiempos[k].append(r[k]["ms"])
    ev["pares"] = pares
    ev["tiempos_ms_por_par"] = {k: {"promedio": promedio(v), "mediana": mediana(v)} for k, v in tiempos.items()}
    ev["estadisticos"] = {}
    for k in CLAVES:
        v = [p["s"][k] for p in pares]
        ev["estadisticos"][k] = {"min": min(v), "max": max(v), "promedio": promedio(v), "rango": max(v) - min(v)}
    ev["spearman"] = {a: {b: spearman([p["s"][a] for p in pares], [p["s"][b] for p in pares]) for b in CLAVES} for a in CLAVES}
    ev["posicion_caso"] = {}
    for k in CLAVES:
        orden = ordenar_por_mezcla(pares, clave=lambda p: p["s"][k], descendente=True)
        pos = [n + 1 for n, p in enumerate(orden) if (p["a"], p["b"]) == (CASO_A, CASO_B)][0]
        ev["posicion_caso"][k] = pos
        ev.setdefault("top5", {})[k] = [(p["a"], p["b"], p["s"][k]) for p in orden[:5]]
    # verificaciones de las explicaciones del analisis critico (no se afirma nada sin medirlo)
    lon = {d["id"]: len(d["pre"]["texto_limpio"]) for d in docs}
    razon = [min(lon[p["a"]], lon[p["b"]]) / max(lon[p["a"]], lon[p["b"]]) for p in pares]
    ev["verif"] = {"spearman_lev_vs_razon_longitud": spearman([p["s"]["levenshtein"] for p in pares], razon),
                   "spearman_nw_vs_razon_longitud": spearman([p["s"]["needleman-wunsch"] for p in pares], razon),
                   "spearman_tfidf_vs_razon_longitud": spearman([p["s"]["tfidf-coseno"] for p in pares], razon), "emb": {}}
    for clave, modelo in corpus.modelos.items():
        vecs = [modelo["vectores"][str(d["id"])] for d in docs]
        dim = len(vecs[0])
        media = [sum(v[k] for v in vecs) / len(vecs) for k in range(dim)]
        cos_media = [coseno(v, media) for v in vecs]
        centrados = [[v[k] - media[k] for k in range(dim)] for v in vecs]
        cc = [coseno(centrados[i], centrados[j]) for i in range(len(vecs)) for j in range(i + 1, len(vecs))]
        cc_pos = [max(0.0, x) for x in cc]
        ev["verif"]["emb"][clave] = {"cos_medio_a_la_media": promedio(cos_media), "cos_min_a_la_media": min(cos_media),
                                     "centrado_min": min(cc), "centrado_max": max(cc), "centrado_rango": max(cc) - min(cc)}
    ev["caso"] = {"a": CASO_A, "b": CASO_B, "contraste": [CONTRASTE_A, CONTRASTE_B]}
    ev["caso_scores"] = {k: [p for p in pares if (p["a"], p["b"]) == (CASO_A, CASO_B)][0]["s"][k] for k in CLAVES}
    ev["contraste_scores"] = {k: [p for p in pares if (p["a"], p["b"]) == (CONTRASTE_A, CONTRASTE_B)][0]["s"][k] for k in CLAVES}

    a, b = corpus.obtener(CASO_A), corpus.obtener(CASO_B)
    ta, tb = a["pre"]["texto_limpio"], b["pre"]["texto_limpio"]
    # programacion dinamica: fragmento corto
    fa, fb = ta[:10], tb[:10]
    lev_m = levenshtein_matriz(fa, fb)
    punt, al_a, al_b, nw_m = needleman_wunsch_alineamiento(fa, fb)
    ev["dp_fragmento"] = {"a": fa, "b": fb, "lev_matriz": lev_m, "lev_distancia": lev_m[len(fa)][len(fb)],
                          "nw_matriz": nw_m, "nw_puntaje": punt, "nw_alineamiento_a": "".join(al_a), "nw_alineamiento_b": "".join(al_b),
                          "nw_normalizado": needleman_wunsch_normalizado(punt, len(fa), len(fb))}
    dist = levenshtein_distancia(ta, tb)
    sc = needleman_wunsch_puntaje(ta, tb)
    ev["dp_completo"] = {"longitud_a": len(ta), "longitud_b": len(tb), "levenshtein": dist,
                         "levenshtein_sim": 1 - dist / max(len(ta), len(tb)), "nw_puntaje": sc,
                         "nw_sim": needleman_wunsch_normalizado(sc, len(ta), len(tb)),
                         "nw_maximo": min(len(ta), len(tb)) - abs(len(ta) - len(tb)), "nw_minimo": -(len(ta) + len(tb))}
    det = detalle_par(corpus, CASO_A, CASO_B, max_terminos=400)
    ev["detalle"] = det
    ev["tokens_caso"] = {"a": a["pre"]["tokens_finales"], "b": b["pre"]["tokens_finales"], "abstract_a": a["abstract"],
                         "abstract_b": b["abstract"], "titulo_a": a["titulo"], "titulo_b": b["titulo"],
                         "texto_limpio_a": ta, "texto_limpio_b": tb}
    ev["pre_ejemplo"] = {k: a["pre"][k] for k in ("minusculas", "sin_signos", "tokens", "tokens_sin_stopwords", "tokens_finales")}
    ev["embeddings_caso"] = {}
    for clave, modelo in corpus.modelos.items():
        va, vb = modelo["vectores"][str(CASO_A)], modelo["vectores"][str(CASO_B)]
        ev["embeddings_caso"][clave] = {
            "modelo": modelo["modelo"], "dimension": modelo["dimension"], "descripcion": modelo["descripcion"],
            "cobertura_a": modelo["cobertura"][str(CASO_A)], "cobertura_b": modelo["cobertura"][str(CASO_B)],
            "primeras_a": va[:6], "primeras_b": vb[:6], "norma_a": coseno(va, va), "coseno": coseno(va, vb),
            "euclidiana": distancia_euclidiana(va, vb), "sim_euclidiana": 1 / (1 + distancia_euclidiana(va, vb))}
    # idf ilustrativos
    idx = corpus.vocab["indice"]
    ev["idf_ejemplos"] = []
    for t in ("aied", "educate", "ai", "researcher"):
        k = idx.obtener(t, -1)
        if k >= 0:
            ev["idf_ejemplos"].append({"termino": t, "df": corpus.vocab["df"][k], "idf": corpus.idf[k]})
    guardar_png("heatmap_tfidf_corpus.png", vz.png_heatmap(
        [[(1.0 if i == j else [p for p in pares if {p["a"], p["b"]} == {docs[i]["id"], docs[j]["id"]}][0]["s"]["tfidf-coseno"])
          for j in range(20)] for i in range(20)], ["#%d" % d["id"] for d in docs], "Coseno TF-IDF entre los 20 abstracts"))
    guardar_png("heatmap_caso.png", vz.png_heatmap(
        [[1.0, ev["caso_scores"]["tfidf-coseno"]], [ev["caso_scores"]["tfidf-coseno"], 1.0]], ["#%d" % CASO_A, "#%d" % CASO_B],
        "Coseno TF-IDF del caso de estudio"))

    # ------------------------------------------------------------------ requerimiento 2
    vectores = [d["tfidf"] for d in docs]
    D = cl.matriz_distancias(vectores)
    comp = cl.comparar_criterios(D)
    ev["clustering"] = {"ids": [d["id"] for d in docs], "titulos": {d["id"]: d["titulo"] for d in docs}, "distancias": D,
                        "mejor": comp["mejor"], "ranking": comp["ranking"], "criterios": {}}
    etiquetas = ["#%d" % d["id"] for d in docs]
    for r in comp["resultados"]:
        alturas = [f["distancia"] for f in r["historial"]]
        grupos = {}
        for k in (3, 4, 5):
            et = cl.cortar_en_k(r["historial"], 20, k)
            g = {}
            for pos, e in enumerate(et):
                g.setdefault(e, []).append(docs[pos]["id"])
            grupos[k] = {"grupos": [g[e] for e in sorted(g)], "silueta": cl.silueta(D, et)}
        ev["clustering"]["criterios"][r["criterio"]] = {
            "nombre": r["nombre"], "historial": r["historial"], "ccc": r["ccc"], "siluetas": r["siluetas"],
            "mejor_k": r["mejor_k"], "mejor_silueta": r["mejor_silueta"], "silueta_promedio_k": r["silueta_promedio_k"],
            "altura_min": min(alturas), "altura_max": max(alturas), "grupos": grupos}
        guardar_png("dendrograma_%s.png" % r["criterio"], vz.png_dendrograma(r["historial"], 20, etiquetas, r["criterio"], r["ccc"], 4))
    guardar_png("clustering_metricas.png", vz.png_metricas_clustering(comp["resultados"]))
    try:  # verificacion opcional contra scipy: SOLO aqui, nunca en src/
        from scipy.cluster.hierarchy import cophenet, linkage
        from scipy.spatial.distance import squareform
        cond = squareform(D, checks=False)
        ver = {}
        for r in comp["resultados"]:
            Z = linkage(cond, method=r["criterio"])
            mias = [f["distancia"] for f in r["historial"]]
            dmax = max(abs(x - y) for x, y in zip(mias, Z[:, 2]))
            ccc_sp, _ = cophenet(Z, cond)
            ver[r["criterio"]] = {"max_dif_alturas": float(dmax), "ccc_scipy": float(ccc_sp), "dif_ccc": float(abs(ccc_sp - r["ccc"]))}
        ev["verificacion_scipy"] = ver
    except Exception as e:  # pragma: no cover
        ev["verificacion_scipy"] = {"error": "scipy no disponible: %s" % e}

    # ------------------------------------------------------------------ requerimiento 3
    d9 = corpus.obtener(DOC_PATRON)
    texto = d9["abstract"]
    lps = kmp_tabla_lps(PATRON.lower())
    prep_bm = bm_preprocesar(PATRON.lower())
    malo = {c: prep_bm["malo"].obtener(c) for c in prep_bm["malo"].claves()}
    ev["patron"] = {"patron": PATRON, "doc": DOC_PATRON, "titulo_doc": d9["titulo"], "texto": texto, "n": len(texto), "m": len(PATRON),
                    "lps": lps, "malo": malo, "bueno": prep_bm["bueno"], "borde": prep_bm["borde"], "algoritmos": {}}
    for alg in ALGORITMOS:
        r = ejecutar(alg, texto, PATRON, True, True)
        ev["patron"]["algoritmos"][alg] = {"posiciones": r["posiciones"], "comparaciones": r["comparaciones"],
                                           "iteraciones": len(r["traza"]), "colisiones": r.get("colisiones", 0),
                                           "traza_inicio": r["traza"][:12]}
    # Rabin-Karp: calculo numerico del hash inicial y rodante
    p_min = PATRON.lower()
    t_min = texto.lower()
    base, mod = 256, 1000000007
    prep = rk_preprocesar(p_min, base, mod)
    h0 = rk_hash(t_min[:len(p_min)], base, mod)
    rodante = []
    h = h0
    for s in range(3):
        nuevo = ((h - ord(t_min[s]) * prep["potencia"]) * base + ord(t_min[s + len(p_min)])) % mod
        rodante.append({"s": s, "hash_ventana": h, "saliente": t_min[s], "entrante": t_min[s + len(p_min)], "hash_siguiente": nuevo,
                        "directo": rk_hash(t_min[s + 1:s + 1 + len(p_min)], base, mod)})
        h = nuevo
    ev["patron"]["rk"] = {"base": base, "modulo": mod, "hash_patron": prep["hash_patron"], "potencia": prep["potencia"],
                          "hash_primera_ventana": h0, "ventana0": t_min[:len(p_min)], "rodante": rodante,
                          "terminos_horner": [{"c": c, "ord": ord(c)} for c in p_min]}
    # efecto del modulo q sobre las colisiones reales (mismo texto y mismo patron)
    ev["patron"]["colisiones_por_modulo"] = []
    for q in (11, 31, 101, 211, 1009, 10007, 1000000007):
        pr = rk_preprocesar(p_min, base, q)
        rr = rk_buscar(t_min, p_min, pr, [])
        ev["patron"]["colisiones_por_modulo"].append({"modulo": q, "hash_patron": pr["hash_patron"], "colisiones": rr["colisiones"],
                                                      "posiciones": rr["posiciones"], "ventanas": len(t_min) - len(p_min) + 1})
    elegido = 101
    ev["patron"]["modulo_demo"] = elegido
    tr = []
    pr = rk_preprocesar(p_min, base, elegido)
    rr = rk_buscar(t_min, p_min, pr, tr)
    ev["patron"]["rk_demo"] = {"modulo": elegido, "hash_patron": pr["hash_patron"], "colisiones": rr["colisiones"],
                               "posiciones": rr["posiciones"],
                               "colisiones_detalle": [dict(e, ventana=t_min[e["s"]:e["s"] + len(p_min)]) for e in tr if e["colision"]][:6],
                               "ventanas_con_hash_igual": [e["s"] for e in tr if e["igual"]][:40]}
    for alg, nombre in (("kmp", "patron_kmp.png"), ("boyer-moore", "patron_boyer_moore.png"), ("rabin-karp", "patron_rabin_karp.png")):
        pos0 = ev["patron"]["algoritmos"][alg]["posiciones"][0]
        ini = max(0, pos0 - 20)
        largo = {"kmp": 120, "boyer-moore": 130, "rabin-karp": 70}[alg]
        frag = texto[ini:ini + largo]
        tr = ejecutar(alg, frag, PATRON, True, True)["traza"]
        guardar_png(nombre, vz.png_alineaciones(frag, PATRON, alg, tr))
        ev["patron"].setdefault("fragmentos", {})[alg] = {"desde": ini, "largo": largo, "texto": frag, "iteraciones": len(tr)}

    # tiempos reales
    texto_corpus = texto_del_corpus(docs)
    patrones = ["ai", "learning", PATRON, "artificial intelligence in education", "systematic review of the literature"]
    ev["benchmark"] = {"n_corpus": len(texto_corpus), "por_patron": []}
    for p in patrones:
        ev["benchmark"]["por_patron"].append({"patron": p, "m": len(p), "resultado": medir(texto_corpus, p, 15)})
    ev["benchmark"]["escalabilidad"] = medir_escalabilidad(texto_corpus, PATRON, (1, 2, 4, 8, 16, 32), 3)
    ev["benchmark"]["sinteticos"] = medir_casos_sinteticos(20000, 40, 3)
    base_r = ev["benchmark"]["por_patron"][2]["resultado"]
    guardar_png("tiempos_corpus.png", vz.png_barras_tiempos(
        "Corpus completo, patron '%s' (mediana de 15 corridas)" % PATRON, ["KMP", "Boyer-Moore", "Rabin-Karp"],
        [base_r[a]["ms_preprocesamiento"] for a in ALGORITMOS], [base_r[a]["ms_busqueda"] for a in ALGORITMOS]))
    esc = ev["benchmark"]["escalabilidad"]
    guardar_png("escalabilidad.png", vz.png_escalabilidad(
        "Tiempo de busqueda vs tamano del texto (patron '%s')" % PATRON, [f["n"] for f in esc],
        {"KMP": [f["algoritmos"]["kmp"]["ms_busqueda"] for f in esc],
         "Boyer-Moore": [f["algoritmos"]["boyer-moore"]["ms_busqueda"] for f in esc],
         "Rabin-Karp": [f["algoritmos"]["rabin-karp"]["ms_busqueda"] for f in esc]}))
    ev["duracion_script_s"] = time.time() - t_inicio
    with open(os.path.join(EVI, "evidencias.json"), "w", encoding="utf-8") as f:
        json.dump(ev, f, ensure_ascii=False, indent=1)
    print("Evidencias guardadas en docs/evidencias/evidencias.json (%.0f s)" % ev["duracion_script_s"])


if __name__ == "__main__":
    main()
