"""Mediciones reales de tiempo (time.perf_counter) para contrastar la Big O teorica con el rendimiento observado."""
import time

from src.estructuras_datos import mediana
from src.patrones import ALGORITMOS, ejecutar


def texto_del_corpus(documentos):
    """Todos los abstracts concatenados (separados por un salto de linea)."""
    partes = ""
    primero = True
    for d in documentos:
        if primero:
            partes = d["abstract"]
            primero = False
        else:
            partes += "\n" + d["abstract"]
    return partes


def medir(texto, patron, repeticiones=5, ignorar_mayusculas=True):
    """Para cada algoritmo: mediana de tiempos de preprocesamiento y de busqueda (ms), comparaciones y ocurrencias."""
    salida = {}
    for a in ALGORITMOS:
        tp, tb = [], []
        ultimo = None
        k = 0
        while k < repeticiones:
            ultimo = ejecutar(a, texto, patron, ignorar_mayusculas)
            tp.append(ultimo["ms_preprocesamiento"])
            tb.append(ultimo["ms_busqueda"])
            k += 1
        salida[a] = {"ms_preprocesamiento": mediana(tp), "ms_busqueda": mediana(tb),
                     "comparaciones": ultimo["comparaciones"], "ocurrencias": len(ultimo["posiciones"]),
                     "colisiones": ultimo.get("colisiones", 0)}
    return salida


def medir_escalabilidad(texto_base, patron, factores=(1, 2, 4, 8, 16), repeticiones=3):
    """Repite el corpus 'factor' veces para ver como crece el tiempo con n."""
    filas = []
    for f in factores:
        t = texto_base
        k = 1
        while k < f:
            t += "\n" + texto_base
            k += 1
        filas.append({"factor": f, "n": len(t), "algoritmos": medir(t, patron, repeticiones)})
    return filas


def medir_casos_sinteticos(n=20000, m=40, repeticiones=3):
    """Casos limite para ver mejor/peor caso (textos sinteticos, no del corpus)."""
    casos = [
        ("Sin ocurrencias, alfabeto distinto (mejor caso de Boyer-Moore)", "a" * n, "b" * m),
        ("Casi coincide siempre: patron a^(m-1)b sobre a^n", "a" * n, "a" * (m - 1) + "b"),
        ("Todas las posiciones coinciden: patron a^m sobre a^n (peor caso de BM y RK)", "a" * n, "a" * m),
    ]
    filas = []
    for nombre, t, p in casos:
        filas.append({"caso": nombre, "n": n, "m": m, "algoritmos": medir(t, p, repeticiones, False)})
    return filas
