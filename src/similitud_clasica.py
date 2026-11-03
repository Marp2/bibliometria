"""Cuatro algoritmos clasicos de similitud, implementados desde cero (listas y bucles).

Todos devuelven una similitud normalizada en [0, 1] (1 = identicos).

  1. Levenshtein            programacion dinamica, O(m*n) tiempo, O(min(m,n)) espacio (O(m*n) si se guarda la matriz)
  2. Needleman-Wunsch       programacion dinamica (alineamiento global), O(m*n)
  3. Coseno con TF-IDF      espacio vectorial, O(V) por par tras construir el vocabulario (V = terminos distintos)
  4. Jaccard                conjuntos con tabla hash, O(m+n) promedio

Levenshtein y Needleman-Wunsch trabajan sobre cualquier secuencia (cadena o lista de palabras).
"""
import math

from src.estructuras_datos import (
    ConjuntoHash, ListaDinamica, TablaHashSimple, crear_matriz, mayor_de_dos, mayor_de_tres,
    ordenar_por_mezcla,
)


# ===========================================================================
# 1. LEVENSHTEIN
# ===========================================================================
def levenshtein_matriz(a, b):
    """Matriz completa D[i][j] = distancia entre a[:i] y b[:j]. Sirve para mostrar el llenado paso a paso."""
    la, lb = len(a), len(b)
    D = crear_matriz(la + 1, lb + 1, 0)
    i = 0
    while i <= la:
        D[i][0] = i
        i += 1
    j = 0
    while j <= lb:
        D[0][j] = j
        j += 1
    i = 1
    while i <= la:
        j = 1
        while j <= lb:
            costo = 0 if a[i - 1] == b[j - 1] else 1
            borrar = D[i - 1][j] + 1
            insertar = D[i][j - 1] + 1
            sustituir = D[i - 1][j - 1] + costo
            mejor = borrar
            if insertar < mejor:
                mejor = insertar
            if sustituir < mejor:
                mejor = sustituir
            D[i][j] = mejor
            j += 1
        i += 1
    return D


def levenshtein_distancia(a, b):
    """Misma recurrencia, pero guardando solo dos filas: espacio O(min(m,n))."""
    if len(a) < len(b):
        a, b = b, a  # b es la secuencia mas corta
    la, lb = len(a), len(b)
    anterior = [0] * (lb + 1)
    j = 0
    while j <= lb:
        anterior[j] = j
        j += 1
    i = 1
    while i <= la:
        actual = [0] * (lb + 1)
        actual[0] = i
        ai = a[i - 1]
        j = 1
        while j <= lb:
            costo = 0 if ai == b[j - 1] else 1
            mejor = anterior[j] + 1
            insertar = actual[j - 1] + 1
            if insertar < mejor:
                mejor = insertar
            sustituir = anterior[j - 1] + costo
            if sustituir < mejor:
                mejor = sustituir
            actual[j] = mejor
            j += 1
        anterior = actual
        i += 1
    return anterior[lb]


def levenshtein_similitud(a, b):
    mayor = mayor_de_dos(len(a), len(b))
    if mayor == 0:
        return 1.0
    return 1.0 - levenshtein_distancia(a, b) / mayor


# ===========================================================================
# 2. NEEDLEMAN-WUNSCH (alineamiento global)
# ===========================================================================
def needleman_wunsch_matriz(a, b, coincide=1, difiere=-1, hueco=-1):
    """Devuelve la matriz F de puntajes. F[i][j] = mejor puntaje de alinear a[:i] con b[:j]."""
    la, lb = len(a), len(b)
    F = crear_matriz(la + 1, lb + 1, 0)
    i = 0
    while i <= la:
        F[i][0] = i * hueco
        i += 1
    j = 0
    while j <= lb:
        F[0][j] = j * hueco
        j += 1
    i = 1
    while i <= la:
        j = 1
        while j <= lb:
            diagonal = F[i - 1][j - 1] + (coincide if a[i - 1] == b[j - 1] else difiere)
            arriba = F[i - 1][j] + hueco
            izquierda = F[i][j - 1] + hueco
            F[i][j] = mayor_de_tres(diagonal, arriba, izquierda)
            j += 1
        i += 1
    return F


def needleman_wunsch_puntaje(a, b, coincide=1, difiere=-1, hueco=-1):
    """Solo el puntaje final, con dos filas (espacio O(n))."""
    la, lb = len(a), len(b)
    anterior = [j * hueco for j in range(lb + 1)]
    i = 1
    while i <= la:
        actual = [0] * (lb + 1)
        actual[0] = i * hueco
        ai = a[i - 1]
        j = 1
        while j <= lb:
            mejor = anterior[j - 1] + (coincide if ai == b[j - 1] else difiere)
            arriba = anterior[j] + hueco
            if arriba > mejor:
                mejor = arriba
            izq = actual[j - 1] + hueco
            if izq > mejor:
                mejor = izq
            actual[j] = mejor
            j += 1
        anterior = actual
        i += 1
    return anterior[lb]


def needleman_wunsch_alineamiento(a, b, coincide=1, difiere=-1, hueco=-1):
    """Traceback desde F[la][lb]. Devuelve (puntaje, alineamiento_a, alineamiento_b, matriz). '-' marca un hueco."""
    F = needleman_wunsch_matriz(a, b, coincide, difiere, hueco)
    i, j = len(a), len(b)
    sal_a = ListaDinamica()
    sal_b = ListaDinamica()
    while i > 0 or j > 0:
        if i > 0 and j > 0 and F[i][j] == F[i - 1][j - 1] + (coincide if a[i - 1] == b[j - 1] else difiere):
            sal_a.agregar(a[i - 1])
            sal_b.agregar(b[j - 1])
            i -= 1
            j -= 1
        elif i > 0 and F[i][j] == F[i - 1][j] + hueco:
            sal_a.agregar(a[i - 1])
            sal_b.agregar("-")
            i -= 1
        else:
            sal_a.agregar("-")
            sal_b.agregar(b[j - 1])
            j -= 1
    sal_a.invertir_en_sitio()
    sal_b.invertir_en_sitio()
    return F[len(a)][len(b)], sal_a.a_lista(), sal_b.a_lista(), F


def needleman_wunsch_normalizado(puntaje, la, lb, coincide=1, difiere=-1, hueco=-1):
    """Normaliza el puntaje a [0,1] con las cotas teoricas:
         maximo = mejor alineamiento posible = coincide*min(la,lb) + hueco*|la-lb|
         minimo = peor alineamiento posible = hueco*(la+lb) (valido si difiere >= 2*hueco)
    """
    menor = la if la < lb else lb
    dif = la - lb if la > lb else lb - la
    maximo = coincide * menor + hueco * dif
    minimo = hueco * (la + lb)
    if maximo == minimo:
        return 1.0
    valor = (puntaje - minimo) / (maximo - minimo)
    if valor < 0.0:
        return 0.0
    if valor > 1.0:
        return 1.0
    return valor


def needleman_wunsch_similitud(a, b, coincide=1, difiere=-1, hueco=-1):
    p = needleman_wunsch_puntaje(a, b, coincide, difiere, hueco)
    return needleman_wunsch_normalizado(p, len(a), len(b), coincide, difiere, hueco)


# ===========================================================================
# 3. COSENO CON TF-IDF
# ===========================================================================
def construir_vocabulario(docs_tokens):
    """docs_tokens: lista de listas de tokens (uno por documento del corpus).
    Devuelve dict con: terminos (orden alfabetico), indice (TablaHashSimple termino->posicion), df, n_docs."""
    vistos = TablaHashSimple(1024)
    for tokens in docs_tokens:
        for t in tokens:
            if not vistos.contiene(t):
                vistos.poner(t, True)
    terminos = ordenar_por_mezcla(vistos.claves())
    indice = TablaHashSimple(len(terminos) * 2 + 16)
    k = 0
    while k < len(terminos):
        indice.poner(terminos[k], k)
        k += 1
    df = [0] * len(terminos)
    for tokens in docs_tokens:
        unicos = ConjuntoHash()
        for t in tokens:
            unicos.agregar(t)
        for t in unicos.elementos():
            df[indice.obtener(t)] += 1
    return {"terminos": terminos, "indice": indice, "df": df, "n_docs": len(docs_tokens)}


def calcular_idf(vocab):
    """IDF suavizado: idf(t) = ln((1 + N) / (1 + df(t))) + 1. Nunca es 0, ni siquiera para terminos presentes en todos los documentos."""
    N = vocab["n_docs"]
    idf = [0.0] * len(vocab["df"])
    k = 0
    while k < len(idf):
        idf[k] = math.log((1 + N) / (1 + vocab["df"][k])) + 1
        k += 1
    return idf


def frecuencias(tokens):
    """Conteo de ocurrencias por termino (TablaHashSimple termino->conteo)."""
    tabla = TablaHashSimple(128)
    for t in tokens:
        tabla.poner(t, tabla.obtener(t, 0) + 1)
    return tabla


def vector_tf(tokens, vocab):
    """TF(t,d) = conteo(t,d) / total de tokens del documento. Vector denso alineado con vocab['terminos']."""
    v = [0.0] * len(vocab["terminos"])
    if len(tokens) == 0:
        return v
    conteo = frecuencias(tokens)
    for t in conteo.claves():
        idx = vocab["indice"].obtener(t, -1)
        if idx >= 0:
            v[idx] = conteo.obtener(t) / len(tokens)
    return v


def vector_tfidf(tokens, vocab, idf):
    tf = vector_tf(tokens, vocab)
    k = 0
    while k < len(tf):
        tf[k] = tf[k] * idf[k]
        k += 1
    return tf


def producto_punto(u, v):
    total = 0.0
    k = 0
    while k < len(u):
        total += u[k] * v[k]
        k += 1
    return total


def norma(u):
    return math.sqrt(producto_punto(u, u))


def coseno_vectores(u, v):
    nu, nv = norma(u), norma(v)
    if nu == 0.0 or nv == 0.0:
        return 0.0
    c = producto_punto(u, v) / (nu * nv)
    if c > 1.0:
        c = 1.0
    if c < -1.0:
        c = -1.0
    return c


def angulo_grados(coseno):
    return math.degrees(math.acos(coseno))


# ===========================================================================
# 4. JACCARD
# ===========================================================================
def jaccard(tokens_a, tokens_b):
    """J(A,B) = |A interseccion B| / |A union B| sobre conjuntos de terminos. Devuelve similitud e intersecciones/union."""
    A = ConjuntoHash()
    B = ConjuntoHash()
    for t in tokens_a:
        A.agregar(t)
    for t in tokens_b:
        B.agregar(t)
    interseccion = ListaDinamica()
    union = ConjuntoHash()
    for t in A.elementos():
        union.agregar(t)
        if B.contiene(t):
            interseccion.agregar(t)
    for t in B.elementos():
        union.agregar(t)
    n_union = union.tamano()
    similitud = interseccion.tamano() / n_union if n_union > 0 else 1.0
    return {
        "similitud": similitud,
        "interseccion": ordenar_por_mezcla(interseccion.a_lista()),
        "union": ordenar_por_mezcla(union.elementos()),
        "tamano_a": A.tamano(),
        "tamano_b": B.tamano(),
    }
