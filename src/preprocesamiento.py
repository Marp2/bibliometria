"""Preprocesamiento de texto escrito a mano (sin re, split, lower, replace ni librerias de NLP).

Pipeline (cada paso es una funcion pura y se puede mostrar por separado en la sustentacion):
  1. a_minusculas      -> unifica 'Education' y 'education'
  2. quitar_tildes     -> unifica 'educación' y 'educacion'
  3. limpiar_signos    -> todo lo que no sea letra se convierte en espacio (se eliminan digitos y puntuacion)
  4. tokenizar         -> separa por espacios
  5. quitar_stopwords  -> descarta palabras vacias (ingles y espanol) y tokens de menos de 2 letras
  6. stem_simple       -> stemming ligero por sufijos (opcional)
"""
from src.estructuras_datos import ListaDinamica, TablaHashSimple

STOPWORDS_EN = (
    "a about above after again against all also am an and any are aren as at be because been before being below "
    "between both but by can cannot could did do does doing don down during each few for from further had has have "
    "having he her here hers herself him himself his how i if in into is it its itself just let me more most my "
    "myself no nor not of off on once only or other our ours ourselves out over own same she should so some such "
    "than that the their theirs them themselves then there these they this those through to too under until up "
    "very was we were what when where which while who whom why will with would you your yours yourself yourselves "
    "may might must shall thus therefore however moreover whereas whether although among within without upon "
    "via per etc ie eg et al use used using based one two three"
)
STOPWORDS_ES = (
    "a al algo algunas algunos ante antes como con contra cual cuando de del desde donde durante e el ella ellas "
    "ellos en entre era erais eran eras eres es esa esas ese eso esos esta estaba estado estamos estan estar este "
    "esto estos fue fueron ha han hasta hay la las le les lo los mas me mi mis mucho muy nada ni no nos nosotros "
    "o os otra otras otro otros para pero poco por porque que quien quienes se sea sean ser si sido sin sobre son "
    "su sus tambien te tiene tienen todo todos tu tus un una uno unos y ya yo"
)

_TABLA_STOPWORDS = None


def _palabras_de_cadena(cadena):
    """Parte una cadena por espacios sin usar split()."""
    resultado = ListaDinamica()
    actual = ""
    i = 0
    while i < len(cadena):
        c = cadena[i]
        if c == " ":
            if actual != "":
                resultado.agregar(actual)
                actual = ""
        else:
            actual += c
        i += 1
    if actual != "":
        resultado.agregar(actual)
    return resultado.a_lista()


def tabla_stopwords():
    global _TABLA_STOPWORDS
    if _TABLA_STOPWORDS is None:
        tabla = TablaHashSimple(512)
        for lista in (STOPWORDS_EN, STOPWORDS_ES):
            for p in _palabras_de_cadena(lista):
                tabla.poner(p, True)
        _TABLA_STOPWORDS = tabla
    return _TABLA_STOPWORDS


# --- Paso 1: minusculas ---------------------------------------------------
def a_minusculas(texto):
    """Convierte A-Z y letras latinas acentuadas mayusculas (U+00C0-U+00DE salvo U+00D7) a minusculas."""
    salida = ListaDinamica(len(texto) + 1)
    i = 0
    while i < len(texto):
        c = texto[i]
        codigo = ord(c)
        if 65 <= codigo <= 90:
            salida.agregar(chr(codigo + 32))
        elif 192 <= codigo <= 222 and codigo != 215:
            salida.agregar(chr(codigo + 32))
        else:
            salida.agregar(c)
        i += 1
    return _unir(salida)


def _unir(lista_caracteres):
    texto = ""
    for c in lista_caracteres:
        texto += c
    return texto


# --- Paso 2: quitar tildes -------------------------------------------------
_ORIGEN = "áàäâãéèëêíìïîóòöôõúùüûñç"
_DESTINO = "aaaaaeeeeiiiiooooouuuunc"


def quitar_tildes(texto):
    salida = ListaDinamica(len(texto) + 1)
    i = 0
    while i < len(texto):
        c = texto[i]
        reemplazo = c
        j = 0
        while j < len(_ORIGEN):
            if _ORIGEN[j] == c:
                reemplazo = _DESTINO[j]
                break
            j += 1
        salida.agregar(reemplazo)
        i += 1
    return _unir(salida)


# --- Paso 3: limpiar signos -----------------------------------------------
def es_letra_ascii(c):
    codigo = ord(c)
    return 97 <= codigo <= 122


def limpiar_signos(texto):
    """Deja solo letras a-z; cualquier otro caracter (digito, signo, guion, apostrofe) pasa a espacio."""
    salida = ListaDinamica(len(texto) + 1)
    i = 0
    while i < len(texto):
        c = texto[i]
        if es_letra_ascii(c):
            salida.agregar(c)
        else:
            salida.agregar(" ")
        i += 1
    return _unir(salida)


# --- Paso 4: tokenizar ----------------------------------------------------
def tokenizar(texto_limpio):
    return _palabras_de_cadena(texto_limpio)


# --- Paso 5: stopwords -----------------------------------------------------
def quitar_stopwords(tokens, longitud_minima=2):
    tabla = tabla_stopwords()
    salida = ListaDinamica()
    for t in tokens:
        if len(t) >= longitud_minima and not tabla.contiene(t):
            salida.agregar(t)
    return salida.a_lista()


# --- Paso 6: stemming simple ----------------------------------------------
# Reglas ordenadas (sufijo, reemplazo, longitud minima de la raiz resultante).
_REGLAS_STEM = (
    ("ational", "ate", 3), ("izations", "ize", 3), ("ization", "ize", 3),
    ("ations", "ate", 3), ("ation", "ate", 3),
    ("ies", "y", 2), ("sses", "ss", 2), ("ings", "", 3), ("ing", "", 3),
    ("ied", "y", 2), ("ed", "", 3), ("ly", "", 3), ("es", "", 3), ("s", "", 3),
)


def _termina_en(palabra, sufijo):
    if len(sufijo) > len(palabra):
        return False
    i = 0
    while i < len(sufijo):
        if palabra[len(palabra) - len(sufijo) + i] != sufijo[i]:
            return False
        i += 1
    return True


def stem_simple(palabra):
    """Stemming ligero: aplica la primera regla que coincide. No toca palabras cortas ni terminadas en 'ss'/'us'/'is'."""
    if len(palabra) <= 3:
        return palabra
    if _termina_en(palabra, "ss") or _termina_en(palabra, "us") or _termina_en(palabra, "is"):
        return palabra
    for sufijo, reemplazo, minimo in _REGLAS_STEM:
        if _termina_en(palabra, sufijo):
            raiz = palabra[:len(palabra) - len(sufijo)]
            if len(raiz) >= minimo:
                return raiz + reemplazo
    return palabra


def aplicar_stemming(tokens):
    salida = ListaDinamica()
    for t in tokens:
        salida.agregar(stem_simple(t))
    return salida.a_lista()


# --- Pipeline completo ----------------------------------------------------
def texto_normalizado(texto):
    """minusculas + sin tildes + sin signos + espacios simples (conserva stopwords). Usado por Levenshtein/Needleman-Wunsch."""
    t = limpiar_signos(quitar_tildes(a_minusculas(texto)))
    return _unir_con_espacio(tokenizar(t))


def _unir_con_espacio(tokens):
    salida = ""
    primero = True
    for t in tokens:
        if primero:
            salida = t
            primero = False
        else:
            salida += " " + t
    return salida


def preprocesar(texto, usar_stemming=True):
    """Devuelve todos los pasos intermedios (para mostrarlos en la web y en la documentacion)."""
    minusculas = a_minusculas(texto)
    sin_tildes = quitar_tildes(minusculas)
    sin_signos = limpiar_signos(sin_tildes)
    tokens = tokenizar(sin_signos)
    sin_stop = quitar_stopwords(tokens)
    stems = aplicar_stemming(sin_stop) if usar_stemming else sin_stop
    return {
        "original": texto,
        "minusculas": minusculas,
        "sin_tildes": sin_tildes,
        "sin_signos": sin_signos,
        "tokens": tokens,
        "tokens_sin_stopwords": sin_stop,
        "tokens_finales": stems,
        "texto_normalizado": _unir_con_espacio(tokens),
        "texto_limpio": _unir_con_espacio(sin_stop),
    }
