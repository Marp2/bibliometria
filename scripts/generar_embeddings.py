"""Genera los embeddings de los 20 abstracts UNA sola vez, fuera del servidor.

La app web (Render plan gratuito) NO carga modelos: solo lee data/processed/embeddings_<modelo>.json.

Modelos (dos obligatorios + uno opcional):
  glove      GloVe wiki-gigaword 300d (Pennington et al., 2014) - vectores de palabras, co-ocurrencia global.
  fasttext   fastText wiki-news-subwords 300d (Mikolov et al., 2018) - vectores de palabras tipo Word2Vec con subpalabras.
  sbert      (OPCIONAL) sentence-transformers all-MiniLM-L6-v2 - modelo de lenguaje tipo Transformer.
             Requiere: pip install sentence-transformers  (descarga el modelo desde Hugging Face).

Metodo para glove/fasttext: embedding del abstract = promedio de los vectores de sus palabras
(tokens en minusculas, sin stopwords, SIN stemming), normalizado a norma 1. Se reporta la cobertura
(palabras con vector / palabras totales).

Uso:
  python scripts/generar_embeddings.py                 # glove + fasttext (descarga ~1.4 GB si no hay archivos locales)
  python scripts/generar_embeddings.py glove           # solo glove
  python scripts/generar_embeddings.py glove --archivo C:/ruta/glove-wiki-gigaword-300.gz
  python scripts/generar_embeddings.py sbert           # opcional
"""
import gzip
import json
import math
import os
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from src.preprocesamiento import preprocesar  # noqa: E402

BASE = "https://github.com/RaRe-Technologies/gensim-data/releases/download/"
MODELOS = {
    "glove": {"nombre": "glove-wiki-gigaword-300", "url": BASE + "glove-wiki-gigaword-300/glove-wiki-gigaword-300.gz",
              "descripcion": "GloVe (Stanford) entrenado con Wikipedia 2014 + Gigaword 5 (6B tokens), 300 dimensiones, 400k palabras."},
    "fasttext": {"nombre": "fasttext-wiki-news-subwords-300",
                 "url": BASE + "fasttext-wiki-news-subwords-300/fasttext-wiki-news-subwords-300.gz",
                 "descripcion": "fastText (Facebook) entrenado con Wikipedia 2017 + UMBC + statmt.org news (16B tokens), 300 dimensiones, 1M palabras."},
}


def cargar_corpus():
    with open(os.path.join(RAIZ, "data", "processed", "corpus.json"), encoding="utf-8") as f:
        return json.load(f)


def descargar(url, destino):
    print("Descargando", url, "->", destino)
    urllib.request.urlretrieve(url, destino)


def leer_vectores(ruta_gz, necesarias):
    """Lee el archivo word2vec-texto (.gz) y conserva solo las palabras necesarias."""
    vectores = {}
    with gzip.open(ruta_gz, "rt", encoding="utf-8", errors="ignore") as f:
        cabecera = f.readline().split()
        dim = int(cabecera[1])
        for linea in f:
            p = linea.find(" ")
            palabra = linea[:p]
            if palabra in necesarias and palabra not in vectores:
                vectores[palabra] = [float(x) for x in linea[p + 1:].split()]
    return vectores, dim


def promedio_normalizado(tokens, vectores, dim):
    suma = [0.0] * dim
    usados = 0
    for t in tokens:
        v = vectores.get(t)
        if v is not None:
            for k in range(dim):
                suma[k] += v[k]
            usados += 1
    if usados == 0:
        return suma, 0
    prom = [x / usados for x in suma]
    n = math.sqrt(sum(x * x for x in prom))
    return [x / n for x in prom], usados


def generar_estatico(clave, archivo=None):
    info = MODELOS[clave]
    corpus = cargar_corpus()
    tokens_por_doc = {d["id"]: preprocesar(d["abstract"], usar_stemming=False)["tokens_sin_stopwords"] for d in corpus}
    necesarias = set()
    for toks in tokens_por_doc.values():
        necesarias.update(toks)
    ruta = archivo or os.path.join(RAIZ, "data", "modelos_cache", info["nombre"] + ".gz")
    if not os.path.exists(ruta):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        descargar(info["url"], ruta)
    vectores, dim = leer_vectores(ruta, necesarias)
    salida, cobertura = {}, {}
    for id_doc, toks in tokens_por_doc.items():
        vec, usados = promedio_normalizado(toks, vectores, dim)
        salida[str(id_doc)] = [round(x, 6) for x in vec]
        cobertura[str(id_doc)] = {"palabras": len(toks), "con_vector": usados,
                                  "cobertura": round(usados / len(toks), 4) if toks else 0}
    datos = {"modelo": info["nombre"], "tipo": "word embeddings promediados", "descripcion": info["descripcion"],
             "dimension": dim, "normalizado_L2": True, "cobertura": cobertura, "vectores": salida}
    guardar(clave, datos)


def generar_sbert():
    from sentence_transformers import SentenceTransformer  # noqa: WPS433 (opcional)
    corpus = cargar_corpus()
    modelo = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    emb = modelo.encode([d["abstract"] for d in corpus], normalize_embeddings=True)
    datos = {"modelo": "all-MiniLM-L6-v2", "tipo": "sentence-transformer (Transformer)",
             "descripcion": "Modelo de oraciones MiniLM-L6 (Reimers y Gurevych, 2019), 384 dimensiones.",
             "dimension": int(emb.shape[1]), "normalizado_L2": True,
             "vectores": {str(d["id"]): [round(float(x), 6) for x in emb[i]] for i, d in enumerate(corpus)}}
    guardar("minilm", datos)


def guardar(clave, datos):
    ruta = os.path.join(RAIZ, "data", "processed", "embeddings_%s.json" % clave)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f)
    print("Guardado", ruta, "(dim %d, %d vectores)" % (datos["dimension"], len(datos["vectores"])))


if __name__ == "__main__":
    args = sys.argv[1:]
    archivo = None
    if "--archivo" in args:
        archivo = args[args.index("--archivo") + 1]
        args = [a for a in args if a not in ("--archivo", archivo)]
    objetivos = args or ["glove", "fasttext"]
    for o in objetivos:
        if o == "sbert":
            generar_sbert()
        elif o in MODELOS:
            generar_estatico(o, archivo)
        else:
            print("Modelo desconocido:", o)
