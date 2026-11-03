"""Similitud con embeddings preentrenados (los vectores se calculan fuera del servidor).

Los vectores de cada abstract se generan UNA sola vez con scripts/generar_embeddings.py y se guardan en
data/processed/embeddings_<modelo>.json. La aplicacion web solo lee esos vectores y calcula a mano:
  - coseno      cos(u,v) = (u.v) / (|u||v|)
  - euclidiana  d(u,v)   = sqrt(sum (u_i - v_i)^2)
"""
import json
import math

from src.estructuras_datos import ordenar_por_mezcla
from src.paths import PROCESSED_DIR, get_configured_processed_dir


def producto_punto(u, v):
    total = 0.0
    k = 0
    while k < len(u):
        total += u[k] * v[k]
        k += 1
    return total


def coseno(u, v):
    nu = math.sqrt(producto_punto(u, u))
    nv = math.sqrt(producto_punto(v, v))
    if nu == 0.0 or nv == 0.0:
        return 0.0
    c = producto_punto(u, v) / (nu * nv)
    if c > 1.0:
        c = 1.0
    if c < -1.0:
        c = -1.0
    return c


def distancia_euclidiana(u, v):
    total = 0.0
    k = 0
    while k < len(u):
        d = u[k] - v[k]
        total += d * d
        k += 1
    return math.sqrt(total)


def similitud_coseno_01(u, v):
    """Coseno recortado a [0,1] (para vectores de texto el coseno negativo es practicamente inexistente)."""
    c = coseno(u, v)
    return c if c > 0.0 else 0.0


def similitud_euclidiana_01(u, v):
    """Convierte la distancia en similitud acotada: 1 / (1 + d). d=0 -> 1; d grande -> 0."""
    return 1.0 / (1.0 + distancia_euclidiana(u, v))


def cargar_modelos(directorios=None):
    """Lee todos los embeddings_*.json disponibles. Devuelve dict nombre_modelo -> datos."""
    import os
    carpetas = directorios or (get_configured_processed_dir(), PROCESSED_DIR)
    modelos = {}
    for carpeta in carpetas:
        if not os.path.isdir(str(carpeta)):
            continue
        for nombre in ordenar_por_mezcla(os.listdir(str(carpeta))):
            if nombre.startswith("embeddings_") and nombre.endswith(".json"):
                clave = nombre[len("embeddings_"):-len(".json")]
                if clave in modelos:
                    continue
                with open(os.path.join(str(carpeta), nombre), encoding="utf-8") as f:
                    datos = json.load(f)
                datos["clave"] = clave
                modelos[clave] = datos
    return modelos
