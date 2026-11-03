"""Requerimiento 1: compara dos o mas abstracts con 4 algoritmos clasicos + 2 modelos de embeddings (IA)."""
import time

from src.estructuras_datos import ListaDinamica, ordenar_por_mezcla
from src.similitud_clasica import (
    angulo_grados, coseno_vectores, jaccard, levenshtein_distancia, needleman_wunsch_normalizado,
    needleman_wunsch_puntaje, norma, producto_punto,
)
from src.similitud_embeddings import (
    coseno, distancia_euclidiana, similitud_coseno_01, similitud_euclidiana_01,
)

CLASICOS = (
    ("levenshtein", "Levenshtein", "Programacion dinamica (distancia de edicion), caracteres sobre texto limpio"),
    ("needleman-wunsch", "Needleman-Wunsch", "Programacion dinamica (alineamiento global), caracteres sobre texto limpio"),
    ("tfidf-coseno", "Coseno con TF-IDF", "Espacio vectorial: TF-IDF implementado a mano, IDF sobre los 20 abstracts"),
    ("jaccard", "Jaccard", "Conjuntos de terminos (con stemming) |A inter B| / |A union B|"),
)
MIN_DOCS, MAX_DOCS = 2, 6


class ErrorComparacion(ValueError):
    pass


def validar_ids(corpus, ids):
    if not isinstance(ids, (list, tuple)):
        raise ErrorComparacion("Debe enviar una lista de identificadores de articulos.")
    unicos = []
    for i in ids:
        d = corpus.obtener(i)  # lanza ErrorCorpus si no existe
        if d["id"] not in unicos:
            unicos.append(d["id"])
    if len(unicos) < MIN_DOCS:
        raise ErrorComparacion("Seleccione al menos %d articulos distintos." % MIN_DOCS)
    if len(unicos) > MAX_DOCS:
        raise ErrorComparacion("Seleccione como maximo %d articulos." % MAX_DOCS)
    return unicos


def _lev(a, b):
    return levenshtein_distancia(a["pre"]["texto_limpio"], b["pre"]["texto_limpio"])


def similitud_par(corpus, a, b):
    """Devuelve dict algoritmo -> {similitud, ms, ...} para un par de documentos (ya obtenidos del corpus)."""
    salida = {}
    ta, tb = a["pre"]["texto_limpio"], b["pre"]["texto_limpio"]
    t0 = time.perf_counter()
    d = levenshtein_distancia(ta, tb)
    mayor = len(ta) if len(ta) > len(tb) else len(tb)
    salida["levenshtein"] = {"similitud": 1.0 - d / mayor if mayor else 1.0, "distancia": d,
                             "ms": (time.perf_counter() - t0) * 1000}
    t0 = time.perf_counter()
    p = needleman_wunsch_puntaje(ta, tb)
    salida["needleman-wunsch"] = {"similitud": needleman_wunsch_normalizado(p, len(ta), len(tb)), "puntaje": p,
                                  "ms": (time.perf_counter() - t0) * 1000}
    t0 = time.perf_counter()
    c = coseno_vectores(a["tfidf"], b["tfidf"])
    salida["tfidf-coseno"] = {"similitud": c if c > 0 else 0.0, "coseno": c, "angulo_grados": angulo_grados(c),
                              "ms": (time.perf_counter() - t0) * 1000}
    t0 = time.perf_counter()
    j = jaccard(a["pre"]["tokens_finales"], b["pre"]["tokens_finales"])
    salida["jaccard"] = {"similitud": j["similitud"], "interseccion": len(j["interseccion"]), "union": len(j["union"]),
                         "ms": (time.perf_counter() - t0) * 1000}
    for clave, modelo in corpus.modelos.items():
        va, vb = modelo["vectores"].get(str(a["id"])), modelo["vectores"].get(str(b["id"]))
        if va is None or vb is None:
            continue
        t0 = time.perf_counter()
        salida["emb-" + clave] = {"similitud": similitud_coseno_01(va, vb), "coseno": coseno(va, vb),
                                  "distancia_euclidiana": distancia_euclidiana(va, vb),
                                  "similitud_euclidiana": similitud_euclidiana_01(va, vb),
                                  "modelo": modelo["modelo"], "ms": (time.perf_counter() - t0) * 1000}
    return salida


def algoritmos_disponibles(corpus):
    lista = [{"clave": c, "nombre": n, "tipo": "clasico", "descripcion": d} for c, n, d in CLASICOS]
    for clave, m in corpus.modelos.items():
        lista.append({"clave": "emb-" + clave, "nombre": "Embeddings: " + m["modelo"], "tipo": "ia",
                      "descripcion": m.get("descripcion", "")})
    return lista


def comparar(corpus, ids):
    ids = validar_ids(corpus, ids)
    docs = [corpus.obtener(i) for i in ids]
    algs = algoritmos_disponibles(corpus)
    pares = []
    matrices = {a["clave"]: [[1.0 if i == j else None for j in range(len(docs))] for i in range(len(docs))] for a in algs}
    i = 0
    while i < len(docs):
        j = i + 1
        while j < len(docs):
            r = similitud_par(corpus, docs[i], docs[j])
            pares.append({"a": docs[i]["id"], "b": docs[j]["id"], "resultados": r})
            for clave in r:
                matrices[clave][i][j] = r[clave]["similitud"]
                matrices[clave][j][i] = r[clave]["similitud"]
            j += 1
        i += 1
    return {"ids": ids, "titulos": {d["id"]: d["titulo"] for d in docs}, "algoritmos": algs,
            "pares": pares, "matrices": matrices}


def detalle_par(corpus, id_a, id_b, max_terminos=40):
    """Calculos intermedios para mostrar/explicar: TF-IDF, Jaccard, DP y embeddings de un par concreto."""
    a, b = corpus.obtener(id_a), corpus.obtener(id_b)
    ta, tb = a["pre"]["tokens_finales"], b["pre"]["tokens_finales"]
    idx = corpus.vocab["indice"]
    filas = []
    for t in ordenar_por_mezcla(jaccard(ta, tb)["union"]):
        k = idx.obtener(t)
        wa, wb = a["tfidf"][k], b["tfidf"][k]
        filas.append({"termino": t, "df": corpus.vocab["df"][k], "idf": corpus.idf[k],
                      "tf_a": wa / corpus.idf[k], "tf_b": wb / corpus.idf[k], "w_a": wa, "w_b": wb, "producto": wa * wb})
    filas = ordenar_por_mezcla(filas, clave=lambda f: f["producto"], descendente=True)
    c = coseno_vectores(a["tfidf"], b["tfidf"])
    jac = jaccard(ta, tb)
    return {
        "a": id_a, "b": id_b,
        "tfidf": {"producto_punto": producto_punto(a["tfidf"], b["tfidf"]), "norma_a": norma(a["tfidf"]),
                  "norma_b": norma(b["tfidf"]), "coseno": c, "angulo_grados": angulo_grados(c),
                  "terminos_union": len(filas), "terminos_mayor_aporte": filas[:max_terminos],
                  "tamano_vocabulario": len(corpus.vocab["terminos"])},
        "jaccard": {"similitud": jac["similitud"], "interseccion": jac["interseccion"], "tamano_union": len(jac["union"]),
                    "tamano_a": jac["tamano_a"], "tamano_b": jac["tamano_b"]},
        "cadenas": {"longitud_a": len(a["pre"]["texto_limpio"]), "longitud_b": len(b["pre"]["texto_limpio"])},
        "similitudes": similitud_par(corpus, a, b),
    }
