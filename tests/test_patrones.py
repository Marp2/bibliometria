import random

import pytest

from src.patrones import (
    ALGORITMOS, ErrorPatron, bm_buscar, bm_tabla_caracter_malo, bm_tabla_sufijo_bueno, buscar_en_corpus, comparar_algoritmos,
    ejecutar, fragmento, kmp_buscar, kmp_tabla_lps, rk_buscar, rk_hash, rk_preprocesar,
)


def ocurrencias_ref(t, p):
    """Referencia INDEPENDIENTE (solo en pruebas): busqueda ingenua con str.find."""
    r, i = [], 0
    while True:
        k = t.find(p, i)
        if k < 0:
            return r
        r.append(k)
        i = k + 1


# ---- tablas auxiliares
def test_lps_ejemplos_clasicos():
    assert kmp_tabla_lps("ABABCABAB") == [0, 0, 1, 2, 0, 1, 2, 3, 4]
    assert kmp_tabla_lps("AAAA") == [0, 1, 2, 3]
    assert kmp_tabla_lps("ABCD") == [0, 0, 0, 0]
    assert kmp_tabla_lps("A") == [0]


def test_boyer_moore_caracter_malo():
    t = bm_tabla_caracter_malo("ABCAB")
    assert (t.obtener("A"), t.obtener("B"), t.obtener("C"), t.obtener("Z", -1)) == (3, 4, 2, -1)


def good_suffix_bruto(p):
    """Definicion directa del corrimiento por sufijo bueno (para contrastar con la tabla construida por bordes)."""
    m = len(p)
    desp = [0] * (m + 1)
    for j in range(m + 1):      # j = posicion del desajuste (j=0 -> sufijo coincidente = p[0..]... se usa indice j-1 del texto)
        pass
    # shift[k] para k = j+1: ya coincidio el sufijo suf = p[k:], fallo p[k-1]
    for k in range(m, -1, -1):
        suf = p[k:]
        mejor = None
        for s in range(1, m + 1):            # s = corrimiento
            # el patron desplazado s posiciones debe ser compatible con el sufijo ya visto
            ok = True
            for idx, ch in enumerate(suf):
                pos = k + idx - s            # posicion en p que quedaria sobre este caracter del texto
                if pos >= 0 and p[pos] != ch:
                    ok = False
                    break
            if ok and k > 0:
                pos_fallo = k - 1 - s        # el caracter que fallo debe ser distinto del que quedaria alineado
                if pos_fallo >= 0 and p[pos_fallo] == p[k - 1]:
                    ok = False
            if ok:
                mejor = s
                break
        desp[k] = mejor if mejor is not None else m
    return desp


@pytest.mark.parametrize("patron", ["ABBABAB", "ANPANMAN", "AAAA", "ABCD", "ABAB", "GCAGAGAG", "abcabcabc"])
def test_sufijo_bueno_coincide_con_definicion(patron):
    desp, _ = bm_tabla_sufijo_bueno(patron)
    m = len(patron)
    bruto = good_suffix_bruto(patron)
    # corrimiento tras fallo en j (k=j+1) con sufijo coincidente no vacio
    for k in range(1, m):
        assert desp[k] == bruto[k], (patron, k, desp, bruto)


# ---- los tres algoritmos coinciden
def test_ocurrencias_superpuestas():
    for a in ALGORITMOS:
        assert ejecutar(a, "aaaa", "aa")["posiciones"] == [0, 1, 2]
        assert ejecutar(a, "abababa", "aba")["posiciones"] == [0, 2, 4]


def test_los_tres_coinciden_con_referencia_en_casos_aleatorios():
    random.seed(11)
    for _ in range(2500):
        alfabeto = random.choice(["ab", "abc", "abcdefgh"])
        t = "".join(random.choice(alfabeto) for _ in range(random.randint(0, 60)))
        p = "".join(random.choice(alfabeto) for _ in range(random.randint(1, 7)))
        esperado = ocurrencias_ref(t, p)
        for a in ALGORITMOS:
            assert ejecutar(a, t, p)["posiciones"] == esperado, (a, t, p)


def test_patron_mas_largo_que_el_texto():
    for a in ALGORITMOS:
        r = ejecutar(a, "abc", "abcdef")
        assert r["posiciones"] == [] and r["comparaciones"] >= 0


def test_patron_igual_al_texto_y_texto_vacio():
    for a in ALGORITMOS:
        assert ejecutar(a, "hola", "hola")["posiciones"] == [0]
        assert ejecutar(a, "", "x")["posiciones"] == []


def test_entradas_invalidas():
    for a in ALGORITMOS:
        with pytest.raises(ErrorPatron):
            ejecutar(a, "texto", "")
        with pytest.raises(ErrorPatron):
            ejecutar(a, None, "x")
        with pytest.raises(ErrorPatron):
            ejecutar(a, "texto", "x" * 500)
    with pytest.raises(ErrorPatron):
        ejecutar("inexistente", "texto", "x")


def test_ignorar_mayusculas_conserva_posiciones():
    texto = "Assessment and ASSESSMENT and assessment"
    for a in ALGORITMOS:
        assert ejecutar(a, texto, "assessment", ignorar_mayusculas=True)["posiciones"] == [0, 15, 30]
        assert ejecutar(a, texto, "assessment", ignorar_mayusculas=False)["posiciones"] == [30]


def test_unicode():
    for a in ALGORITMOS:
        assert ejecutar(a, "educación y educación", "ción")["posiciones"] == [5, 17]


# ---- Rabin-Karp: hash rodante y colisiones
def test_rabin_karp_hash_rodante_igual_al_directo():
    t, m = "algoritmos de busqueda", 5
    base, mod = 256, 1000000007
    prep = rk_preprocesar("x" * m, base, mod)
    h = rk_hash(t[:m], base, mod)
    for s in range(len(t) - m):
        h = ((h - ord(t[s]) * prep["potencia"]) * base + ord(t[s + m])) % mod
        assert h == rk_hash(t[s + 1:s + 1 + m], base, mod)


def test_rabin_karp_con_modulo_pequeno_genera_colisiones_pero_resultado_correcto():
    random.seed(5)
    t = "".join(random.choice("abcd") for _ in range(400))
    p = "abcab"
    prep = rk_preprocesar(p, 256, 13)   # modulo diminuto: muchas colisiones
    r = rk_buscar(t, p, prep)
    assert r["posiciones"] == ocurrencias_ref(t, p)
    assert r["colisiones"] > 0


def test_rabin_karp_modulo_grande_sin_colisiones_en_el_corpus(corpus):
    total = 0
    for d in corpus.documentos:
        total += ejecutar("rabin-karp", d["abstract"], "assessment", True)["colisiones"]
    assert total == 0


# ---- corpus
@pytest.mark.parametrize("patron", ["assessment", "AI", "learning", "ChatGPT", "systematic review", "zzzz", "e", "a "])
def test_tres_algoritmos_coinciden_en_el_corpus(corpus, patron):
    r = comparar_algoritmos(corpus.documentos, patron, True)
    assert r["coinciden"] is True
    totales = {a: r["algoritmos"][a]["total"] for a in ALGORITMOS}
    assert len(set(totales.values())) == 1


def test_buscar_en_corpus_resalta_la_coincidencia(corpus):
    r = buscar_en_corpus(corpus.documentos, "assessment", "boyer-moore", True)
    assert r["total"] > 0
    for doc in r["resultados"]:
        abstract = corpus.obtener(doc["id"])["abstract"]
        for o in doc["ocurrencias"]:
            assert abstract[o["posicion"]:o["posicion"] + 10].lower() == "assessment"
            assert o["coincidencia"].lower() == "assessment"


def test_fragmento_en_los_bordes():
    f = fragmento("abcdef", 0, 2, 10)
    assert f["antes"] == "" and f["coincidencia"] == "ab" and f["despues"] == "cdef" and not f["recortado_inicio"]
    f = fragmento("x" * 200 + "ab" + "y" * 200, 200, 2, 5)
    assert f["recortado_inicio"] and f["recortado_fin"] and len(f["antes"]) == 5
