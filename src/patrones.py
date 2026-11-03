"""Busqueda exacta de patrones (string matching) desde cero: KMP, Boyer-Moore y Rabin-Karp.

Sin find(), index(), 'in', replace() ni expresiones regulares. Los tres algoritmos devuelven TODAS las ocurrencias
(incluidas las superpuestas) como posiciones base 0 en el texto, y cuentan las comparaciones de caracteres.

Complejidades (n = longitud del texto, m = longitud del patron, s = tamano del alfabeto):
  KMP          preprocesamiento O(m)        busqueda  mejor/prom/peor O(n)
  Boyer-Moore  preprocesamiento O(m + s)    busqueda  mejor O(n/m), promedio ~O(n), peor O(n*m) solo con caracter malo;
                                            con sufijo bueno + regla de Galil seria O(n) (aqui: caracter malo + sufijo bueno)
  Rabin-Karp   preprocesamiento O(m)        busqueda  mejor/promedio O(n + m), peor O(n*m) (muchas colisiones)
"""
import time

from src.estructuras_datos import TablaHashSimple, mayor_de_dos, potencia_modular
from src.preprocesamiento import a_minusculas

ALGORITMOS = ("kmp", "boyer-moore", "rabin-karp")
NOMBRES = {"kmp": "Knuth-Morris-Pratt", "boyer-moore": "Boyer-Moore", "rabin-karp": "Rabin-Karp"}
MAX_PATRON = 200


class ErrorPatron(ValueError):
    """Entrada invalida (patron vacio, tipos incorrectos...)."""


def validar_entradas(texto, patron):
    if not isinstance(texto, str):
        raise ErrorPatron("El texto debe ser una cadena.")
    if not isinstance(patron, str):
        raise ErrorPatron("El patron debe ser una cadena.")
    if len(patron) == 0:
        raise ErrorPatron("El patron no puede estar vacio.")
    if len(patron) > MAX_PATRON:
        raise ErrorPatron("El patron supera el maximo de %d caracteres." % MAX_PATRON)


# ===========================================================================
# KMP
# ===========================================================================
def kmp_tabla_lps(patron):
    """lps[i] = longitud del prefijo propio mas largo de patron[0..i] que tambien es sufijo de patron[0..i]."""
    m = len(patron)
    lps = [0] * m
    largo = 0
    i = 1
    while i < m:
        if patron[i] == patron[largo]:
            largo += 1
            lps[i] = largo
            i += 1
        elif largo > 0:
            largo = lps[largo - 1]      # retroceder en el patron, NUNCA en el texto
        else:
            lps[i] = 0
            i += 1
    return lps


def kmp_buscar(texto, patron, lps=None, traza=None):
    n, m = len(texto), len(patron)
    if lps is None:
        lps = kmp_tabla_lps(patron)
    posiciones = []
    comparaciones = 0
    i = 0   # indice en el texto
    j = 0   # caracteres del patron ya emparejados
    while i < n:
        comparaciones += 1
        if texto[i] == patron[j]:
            if traza is not None:
                traza.append({"i": i, "j": j, "ok": True, "s": i - j})
            i += 1
            j += 1
            if j == m:
                posiciones.append(i - m)
                j = lps[j - 1]          # permite ocurrencias superpuestas
        else:
            if traza is not None:
                traza.append({"i": i, "j": j, "ok": False, "s": i - j})
            if j > 0:
                j = lps[j - 1]
            else:
                i += 1
    return {"posiciones": posiciones, "comparaciones": comparaciones}


# ===========================================================================
# BOYER-MOORE (caracter malo + sufijo bueno)
# ===========================================================================
def bm_tabla_caracter_malo(patron):
    """ultima[c] = ultima posicion de c en el patron (se consulta con defecto -1)."""
    tabla = TablaHashSimple(64)
    i = 0
    while i < len(patron):
        tabla.poner(patron[i], i)
        i += 1
    return tabla


def bm_tabla_sufijo_bueno(patron):
    """Devuelve (desplazamiento, borde). desplazamiento[j+1] = corrimiento cuando falla la comparacion en patron[j]
    y ya coincidio el sufijo patron[j+1..]. desplazamiento[0] = corrimiento tras una coincidencia completa."""
    m = len(patron)
    borde = [0] * (m + 1)
    desp = [0] * (m + 1)
    i = m
    j = m + 1
    borde[i] = j
    while i > 0:
        while j <= m and patron[i - 1] != patron[j - 1]:
            if desp[j] == 0:
                desp[j] = j - i
            j = borde[j]
        i -= 1
        j -= 1
        borde[i] = j
    j = borde[0]
    i = 0
    while i <= m:
        if desp[i] == 0:
            desp[i] = j
        if i == j:
            j = borde[j]
        i += 1
    return desp, borde


def bm_preprocesar(patron):
    desp, borde = bm_tabla_sufijo_bueno(patron)
    return {"malo": bm_tabla_caracter_malo(patron), "bueno": desp, "borde": borde}


def bm_buscar(texto, patron, tablas=None, traza=None):
    n, m = len(texto), len(patron)
    if tablas is None:
        tablas = bm_preprocesar(patron)
    malo, bueno = tablas["malo"], tablas["bueno"]
    posiciones = []
    comparaciones = 0
    s = 0
    while s <= n - m:
        j = m - 1
        while j >= 0:
            comparaciones += 1
            if patron[j] != texto[s + j]:
                break
            j -= 1
        if j < 0:
            posiciones.append(s)
            desplazamiento = bueno[0]
            if traza is not None:
                traza.append({"s": s, "j": -1, "comparados": m, "desplazamiento": desplazamiento,
                              "regla": "coincidencia completa (sufijo bueno)", "malo": None, "bueno": bueno[0]})
            s += desplazamiento
        else:
            por_malo = j - malo.obtener(texto[s + j], -1)
            por_bueno = bueno[j + 1]
            desplazamiento = mayor_de_dos(por_malo, por_bueno)
            if traza is not None:
                traza.append({"s": s, "j": j, "comparados": m - j, "desplazamiento": desplazamiento,
                              "regla": "caracter malo" if por_malo >= por_bueno else "sufijo bueno",
                              "malo": por_malo, "bueno": por_bueno, "caracter_texto": texto[s + j]})
            s += desplazamiento
    return {"posiciones": posiciones, "comparaciones": comparaciones}


# ===========================================================================
# RABIN-KARP (rolling hash)
# ===========================================================================
BASE_RK = 256
MODULO_RK = 1000000007   # primo grande -> colisiones muy improbables


def rk_hash(cadena, base, modulo):
    """Hash polinomial por Horner: h = (c0*b^(m-1) + c1*b^(m-2) + ... + c(m-1)) mod q."""
    h = 0
    i = 0
    while i < len(cadena):
        h = (h * base + ord(cadena[i])) % modulo
        i += 1
    return h


def rk_preprocesar(patron, base=BASE_RK, modulo=MODULO_RK):
    m = len(patron)
    return {"hash_patron": rk_hash(patron, base, modulo), "potencia": potencia_modular(base, m - 1, modulo),
            "base": base, "modulo": modulo}


def rk_buscar(texto, patron, prep=None, traza=None):
    n, m = len(texto), len(patron)
    if prep is None:
        prep = rk_preprocesar(patron)
    base, modulo, hp, pot = prep["base"], prep["modulo"], prep["hash_patron"], prep["potencia"]
    posiciones = []
    comparaciones = 0
    colisiones = 0
    if m > n:
        return {"posiciones": posiciones, "comparaciones": 0, "colisiones": 0}
    h = rk_hash(texto[:m], base, modulo)
    s = 0
    while s <= n - m:
        if h == hp:
            # el hash coincide: puede ser coincidencia real o COLISION -> se verifica caracter por caracter
            k = 0
            while k < m:
                comparaciones += 1
                if texto[s + k] != patron[k]:
                    break
                k += 1
            real = (k == m)
            if real:
                posiciones.append(s)
            else:
                colisiones += 1
            if traza is not None:
                traza.append({"s": s, "hash": h, "hash_patron": hp, "igual": True, "real": real,
                              "colision": not real})
        elif traza is not None:
            traza.append({"s": s, "hash": h, "hash_patron": hp, "igual": False, "real": False, "colision": False})
        if s < n - m:
            # hash rodante: quitar texto[s], desplazar una posicion y agregar texto[s+m]
            h = ((h - ord(texto[s]) * pot) * base + ord(texto[s + m])) % modulo
        s += 1
    return {"posiciones": posiciones, "comparaciones": comparaciones, "colisiones": colisiones}


# ===========================================================================
# Interfaz comun
# ===========================================================================
def _normalizar(texto, patron, ignorar_mayusculas):
    if ignorar_mayusculas:
        # a_minusculas conserva la longitud: las posiciones siguen valiendo para el texto original
        return a_minusculas(texto), a_minusculas(patron)
    return texto, patron


def ejecutar(algoritmo, texto, patron, ignorar_mayusculas=False, traza=False):
    """Ejecuta un algoritmo midiendo por separado preprocesamiento y busqueda (en milisegundos)."""
    validar_entradas(texto, patron)
    t, p = _normalizar(texto, patron, ignorar_mayusculas)
    eventos = [] if traza else None
    if algoritmo == "kmp":
        t0 = time.perf_counter()
        prep = kmp_tabla_lps(p)
        t1 = time.perf_counter()
        res = kmp_buscar(t, p, prep, eventos)
        extras = {"lps": prep}
    elif algoritmo == "boyer-moore":
        t0 = time.perf_counter()
        prep = bm_preprocesar(p)
        t1 = time.perf_counter()
        res = bm_buscar(t, p, prep, eventos)
        extras = {"bueno": prep["bueno"], "malo": {c: prep["malo"].obtener(c) for c in prep["malo"].claves()}}
    elif algoritmo == "rabin-karp":
        t0 = time.perf_counter()
        prep = rk_preprocesar(p)
        t1 = time.perf_counter()
        res = rk_buscar(t, p, prep, eventos)
        extras = {"hash_patron": prep["hash_patron"], "base": prep["base"], "modulo": prep["modulo"]}
    else:
        raise ErrorPatron("Algoritmo desconocido: %r (use kmp, boyer-moore o rabin-karp)" % (algoritmo,))
    t2 = time.perf_counter()
    res["ms_preprocesamiento"] = (t1 - t0) * 1000.0
    res["ms_busqueda"] = (t2 - t1) * 1000.0
    res["algoritmo"] = algoritmo
    res["extras"] = extras
    if traza:
        res["traza"] = eventos
    return res


def fragmento(texto, posicion, largo, contexto=60):
    """Divide el texto en (antes, coincidencia, despues) para resaltar la coincidencia en la interfaz."""
    ini = posicion - contexto
    if ini < 0:
        ini = 0
    fin = posicion + largo + contexto
    if fin > len(texto):
        fin = len(texto)
    return {"antes": texto[ini:posicion], "coincidencia": texto[posicion:posicion + largo],
            "despues": texto[posicion + largo:fin], "recortado_inicio": ini > 0, "recortado_fin": fin < len(texto)}


def buscar_en_corpus(documentos, patron, algoritmo="kmp", ignorar_mayusculas=True, contexto=60):
    """Busca el patron en el abstract de cada documento. Devuelve ocurrencias por documento y totales."""
    resultados = []
    total = 0
    ms_prep = 0.0
    ms_bus = 0.0
    for d in documentos:
        r = ejecutar(algoritmo, d["abstract"], patron, ignorar_mayusculas)
        ms_prep += r["ms_preprocesamiento"]
        ms_bus += r["ms_busqueda"]
        if len(r["posiciones"]) > 0:
            total += len(r["posiciones"])
            resultados.append({
                "id": d["id"], "titulo": d["titulo"], "cantidad": len(r["posiciones"]),
                "ocurrencias": [{"posicion": p, **fragmento(d["abstract"], p, len(patron), contexto)} for p in r["posiciones"]],
            })
    return {"patron": patron, "algoritmo": algoritmo, "total": total, "documentos_con_coincidencias": len(resultados),
            "resultados": resultados, "ms_preprocesamiento": ms_prep, "ms_busqueda": ms_bus}


def comparar_algoritmos(documentos, patron, ignorar_mayusculas=True):
    """Corre los tres algoritmos sobre todo el corpus y verifica que devuelvan exactamente las mismas posiciones."""
    por_algoritmo = {}
    igual = True
    base = None
    for a in ALGORITMOS:
        posiciones = {}
        ms_p = ms_b = 0.0
        comps = 0
        colisiones = 0
        for d in documentos:
            r = ejecutar(a, d["abstract"], patron, ignorar_mayusculas)
            posiciones[d["id"]] = r["posiciones"]
            ms_p += r["ms_preprocesamiento"]
            ms_b += r["ms_busqueda"]
            comps += r["comparaciones"]
            colisiones += r.get("colisiones", 0)
        if base is None:
            base = posiciones
        elif posiciones != base:
            igual = False
        total = 0
        for k in posiciones:
            total += len(posiciones[k])
        por_algoritmo[a] = {"total": total, "ms_preprocesamiento": ms_p, "ms_busqueda": ms_b,
                            "comparaciones": comps, "colisiones": colisiones, "posiciones": posiciones}
    return {"coinciden": igual, "algoritmos": por_algoritmo}
