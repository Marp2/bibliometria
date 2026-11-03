"""Utilidades para armar Markdown a partir de las evidencias (sin inventar numeros)."""


def tabla(cabeceras, filas, numericas=()):
    """Tabla pipe de Markdown. El numero de guiones del separador fija el ancho relativo de cada columna (pandoc)."""
    n = len(cabeceras)
    largos = [len(str(c)) for c in cabeceras]
    for fila in filas:
        for i in range(n):
            largos[i] = max(largos[i], min(80, len(str(fila[i]))))
    anchos = [max(12, min(70, largos[i])) for i in range(n)]
    sep = []
    for i in range(n):
        if i in numericas:
            sep.append("-" * (anchos[i] - 1) + ":")
        else:
            sep.append("-" * anchos[i])
    lineas = ["| " + " | ".join(cabeceras) + " |", "|" + "|".join(sep) + "|"]
    for fila in filas:
        lineas.append("| " + " | ".join(str(x).replace("|", "/") for x in fila) + " |")
    return "\n".join(lineas) + "\n"


def f(x, d=4):
    return ("%." + str(d) + "f") % x


def matriz_dp(M, a, b):
    cab = ["", ""] + list(b)
    filas = []
    for i in range(len(M)):
        filas.append([("" if i == 0 else a[i - 1])] + [str(v) for v in M[i]])
    return tabla(["a \\ b", "-"] + list(b), [[("-" if i == 0 else a[i - 1])] + [str(v) for v in M[i]] for i in range(len(M))],
                 numericas=range(1, len(b) + 2))


def etiqueta(idx, n=20):
    return "#%d" % (idx + 1) if idx < n else "C%d" % idx


def historial_md(hist, n=20):
    filas = []
    for i, h in enumerate(hist):
        filas.append([i + 1, etiqueta(h["a"], n), etiqueta(h["b"], n), f(h["distancia"]), h["tamano"], "C%d" % h["nuevo"]])
    return tabla(["Paso", "Une", "con", "Distancia", "Tamano", "Nuevo cluster"], filas, numericas=(0, 3, 4))
