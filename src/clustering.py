"""Clustering jerarquico aglomerativo desde cero: Single, Complete y Average Linkage (UPGMA).

Flujo:  vectores TF-IDF -> matriz de distancias (1 - coseno) -> fusiones sucesivas (historial) -> dendrograma.
El historial tiene el mismo formato que una matriz de enlace clasica:
    cada fila = {"a": id_cluster, "b": id_cluster, "distancia": h, "tamano": n, "nuevo": id_nuevo}
Los clusters 0..n-1 son las hojas (documentos); los nuevos clusters se numeran n, n+1, ...

Metricas internas implementadas a mano:
  - coeficiente de correlacion cofenetica (CCC): Pearson entre distancias originales y cofeneticas.
  - coeficiente de silueta promedio para un corte del arbol en k grupos.
Complejidad de esta implementacion: O(n^3) tiempo, O(n^2) espacio (n = 20 documentos -> instantaneo).
"""
import math

from src.estructuras_datos import (
    ListaDinamica, crear_matriz, ordenar_por_mezcla, promedio,
)
from src.similitud_clasica import coseno_vectores

CRITERIOS = ("single", "complete", "average")
NOMBRES = {"single": "Single Linkage (enlace simple)", "complete": "Complete Linkage (enlace completo)",
           "average": "Average Linkage (UPGMA)"}


def matriz_distancias(vectores):
    """D[i][j] = 1 - coseno(vi, vj). Simetrica, diagonal 0, valores en [0,1] para TF-IDF (vectores no negativos)."""
    n = len(vectores)
    D = crear_matriz(n, n, 0.0)
    i = 0
    while i < n:
        j = i + 1
        while j < n:
            d = 1.0 - coseno_vectores(vectores[i], vectores[j])
            if d < 0.0:
                d = 0.0
            D[i][j] = d
            D[j][i] = d
            j += 1
        i += 1
    return D


def _distancia_clusters(D, miembros_a, miembros_b, criterio):
    """Distancia entre dos clusters a partir de la matriz original (definicion directa de cada criterio)."""
    if criterio == "single":
        mejor = None
        for i in miembros_a:
            for j in miembros_b:
                if mejor is None or D[i][j] < mejor:
                    mejor = D[i][j]
        return mejor
    if criterio == "complete":
        mejor = None
        for i in miembros_a:
            for j in miembros_b:
                if mejor is None or D[i][j] > mejor:
                    mejor = D[i][j]
        return mejor
    if criterio == "average":
        total = 0.0
        for i in miembros_a:
            for j in miembros_b:
                total += D[i][j]
        return total / (len(miembros_a) * len(miembros_b))
    raise ValueError("Criterio de enlace desconocido: %r (use single, complete o average)" % (criterio,))


def agrupar(D, criterio):
    """Devuelve el historial de fusiones (n-1 filas). Desempate determinista: menor distancia, luego menor (a,b)."""
    n = len(D)
    if n < 2:
        raise ValueError("Se necesitan al menos 2 documentos para agrupar.")
    activos = ListaDinamica()          # ids de clusters activos
    miembros = {}                      # id cluster -> lista de documentos
    i = 0
    while i < n:
        activos.agregar(i)
        miembros[i] = [i]
        i += 1
    historial = []
    siguiente = n
    while activos.tamano() > 1:
        mejor_d, mejor_a, mejor_b = None, -1, -1
        p = 0
        while p < activos.tamano():
            q = p + 1
            while q < activos.tamano():
                a, b = activos[p], activos[q]
                d = _distancia_clusters(D, miembros[a], miembros[b], criterio)
                if mejor_d is None or d < mejor_d - 1e-15:
                    mejor_d, mejor_a, mejor_b = d, a, b
                q += 1
            p += 1
        nuevos = miembros[mejor_a] + miembros[mejor_b]
        historial.append({"a": mejor_a, "b": mejor_b, "distancia": mejor_d, "tamano": len(nuevos), "nuevo": siguiente})
        miembros[siguiente] = nuevos
        nueva_lista = ListaDinamica()
        for c in activos:
            if c != mejor_a and c != mejor_b:
                nueva_lista.agregar(c)
        nueva_lista.agregar(siguiente)
        activos = nueva_lista
        siguiente += 1
    return historial


def miembros_por_cluster(historial, n):
    """Diccionario id_cluster -> lista de documentos para todos los clusters (hojas y fusiones)."""
    miembros = {}
    i = 0
    while i < n:
        miembros[i] = [i]
        i += 1
    for f in historial:
        miembros[f["nuevo"]] = miembros[f["a"]] + miembros[f["b"]]
    return miembros


# ---------------------------------------------------------------------------
# Metricas internas
# ---------------------------------------------------------------------------
def distancias_cofeneticas(historial, n):
    """C[i][j] = altura de la fusion en la que i y j quedan por primera vez en el mismo cluster."""
    C = crear_matriz(n, n, 0.0)
    miembros = {}
    i = 0
    while i < n:
        miembros[i] = [i]
        i += 1
    for f in historial:
        for i in miembros[f["a"]]:
            for j in miembros[f["b"]]:
                C[i][j] = f["distancia"]
                C[j][i] = f["distancia"]
        miembros[f["nuevo"]] = miembros[f["a"]] + miembros[f["b"]]
    return C


def pearson(x, y):
    n = len(x)
    mx, my = promedio(x), promedio(y)
    sxy = sxx = syy = 0.0
    k = 0
    while k < n:
        dx, dy = x[k] - mx, y[k] - my
        sxy += dx * dy
        sxx += dx * dx
        syy += dy * dy
        k += 1
    if sxx == 0.0 or syy == 0.0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def correlacion_cofenetica(D, historial):
    """CCC: Pearson entre los n(n-1)/2 pares de D y los mismos pares de la matriz cofenetica. Mas cerca de 1 = mejor."""
    n = len(D)
    C = distancias_cofeneticas(historial, n)
    x, y = [], []
    i = 0
    while i < n:
        j = i + 1
        while j < n:
            x.append(D[i][j])
            y.append(C[i][j])
            j += 1
        i += 1
    return pearson(x, y)


def cortar_en_k(historial, n, k):
    """Etiquetas de grupo (0..k-1) por documento al deshacer las ultimas k-1 fusiones."""
    if k < 1 or k > n:
        raise ValueError("k debe estar entre 1 y %d" % n)
    usadas = n - k  # numero de fusiones que se conservan
    miembros = {}
    i = 0
    while i < n:
        miembros[i] = [i]
        i += 1
    vivos = {}
    i = 0
    while i < n:
        vivos[i] = True
        i += 1
    paso = 0
    while paso < usadas:
        f = historial[paso]
        miembros[f["nuevo"]] = miembros[f["a"]] + miembros[f["b"]]
        del vivos[f["a"]]
        del vivos[f["b"]]
        vivos[f["nuevo"]] = True
        paso += 1
    etiquetas = [0] * n
    numero = 0
    for c in ordenar_por_mezcla(list(vivos.keys())):
        for doc in miembros[c]:
            etiquetas[doc] = numero
        numero += 1
    return etiquetas


def silueta(D, etiquetas):
    """Silueta promedio. s(i) = (b-a)/max(a,b), a = distancia media intra-grupo, b = menor distancia media a otro grupo.
    Los grupos de un solo elemento aportan s = 0."""
    n = len(D)
    k = 0
    for e in etiquetas:
        if e + 1 > k:
            k = e + 1
    if k < 2:
        return 0.0
    total = 0.0
    i = 0
    while i < n:
        suma = [0.0] * k
        cuenta = [0] * k
        j = 0
        while j < n:
            if j != i:
                suma[etiquetas[j]] += D[i][j]
                cuenta[etiquetas[j]] += 1
            j += 1
        if cuenta[etiquetas[i]] == 0:
            s = 0.0
        else:
            a = suma[etiquetas[i]] / cuenta[etiquetas[i]]
            b = None
            g = 0
            while g < k:
                if g != etiquetas[i] and cuenta[g] > 0:
                    m = suma[g] / cuenta[g]
                    if b is None or m < b:
                        b = m
                g += 1
            mayor = a if a > b else b
            s = 0.0 if mayor == 0.0 else (b - a) / mayor
        total += s
        i += 1
    return total / n


def siluetas_por_k(D, historial, k_min=2, k_max=8):
    n = len(D)
    resultado = []
    k = k_min
    while k <= k_max and k < n:
        resultado.append({"k": k, "silueta": silueta(D, cortar_en_k(historial, n, k))})
        k += 1
    return resultado


def evaluar(D, criterio, k_min=2, k_max=8):
    historial = agrupar(D, criterio)
    por_k = siluetas_por_k(D, historial, k_min, k_max)
    mejor = por_k[0]
    for r in por_k:
        if r["silueta"] > mejor["silueta"]:
            mejor = r
    return {"criterio": criterio, "nombre": NOMBRES[criterio], "historial": historial,
            "ccc": correlacion_cofenetica(D, historial), "siluetas": por_k,
            "mejor_k": mejor["k"], "mejor_silueta": mejor["silueta"],
            "silueta_promedio_k": promedio([r["silueta"] for r in por_k])}


def comparar_criterios(D, k_min=2, k_max=8):
    """Evalua los tres criterios y elige el mas coherente: mayor CCC; el desempate usa la mejor silueta."""
    resultados = [evaluar(D, c, k_min, k_max) for c in CRITERIOS]
    ordenados = ordenar_por_mezcla(resultados, clave=lambda r: (round(r["ccc"], 6), r["mejor_silueta"]), descendente=True)
    return {"resultados": resultados, "mejor": ordenados[0]["criterio"],
            "ranking": [r["criterio"] for r in ordenados]}


# ---------------------------------------------------------------------------
# Orden de hojas y coordenadas del dendrograma (a partir de MI historial)
# ---------------------------------------------------------------------------
def orden_hojas(historial, n):
    hijos = {}
    for f in historial:
        hijos[f["nuevo"]] = (f["a"], f["b"])
    raiz = historial[-1]["nuevo"]
    orden = []
    pila = [raiz]
    while len(pila) > 0:
        c = pila.pop()
        if c < n:
            orden.append(c)
        else:
            a, b = hijos[c]
            pila.append(b)  # se apila b primero para visitar a antes
            pila.append(a)
    return orden


def coordenadas_dendrograma(historial, n):
    """Devuelve (orden_hojas, segmentos): cada segmento = (x1,y1,x2,y2) listo para dibujar con matplotlib."""
    orden = orden_hojas(historial, n)
    x = {}
    y = {}
    pos = 0
    while pos < n:
        x[orden[pos]] = float(pos)
        y[orden[pos]] = 0.0
        pos += 1
    segmentos = []
    for f in historial:
        xa, ya, xb, yb, h = x[f["a"]], y[f["a"]], x[f["b"]], y[f["b"]], f["distancia"]
        segmentos.append((xa, ya, xa, h))
        segmentos.append((xb, yb, xb, h))
        segmentos.append((xa, h, xb, h))
        x[f["nuevo"]] = (xa + xb) / 2.0
        y[f["nuevo"]] = h
    return orden, segmentos
