import math

import pytest

from src.similitud_clasica import (
    angulo_grados, calcular_idf, construir_vocabulario, coseno_vectores, jaccard, levenshtein_distancia, levenshtein_matriz,
    levenshtein_similitud, needleman_wunsch_alineamiento, needleman_wunsch_matriz, needleman_wunsch_normalizado,
    needleman_wunsch_puntaje, needleman_wunsch_similitud, vector_tf, vector_tfidf,
)
from src.similitud_embeddings import coseno, distancia_euclidiana, similitud_coseno_01, similitud_euclidiana_01


# ---- Levenshtein
def test_levenshtein_casos_conocidos():
    assert levenshtein_distancia("kitten", "sitting") == 3
    assert levenshtein_distancia("flaw", "lawn") == 2
    assert levenshtein_distancia("education", "educational") == 2
    assert levenshtein_distancia("", "abc") == 3 and levenshtein_distancia("abc", "") == 3 and levenshtein_distancia("", "") == 0
    assert levenshtein_distancia("abc", "abc") == 0


def test_levenshtein_matriz_y_dos_filas_coinciden():
    M = levenshtein_matriz("kitten", "sitting")
    assert M[6][7] == 3 and M[0][3] == 3 and M[3][0] == 3
    assert M[1][1] == 1 and M[2][2] == 1  # "k"->"s" cuesta 1; "ki"->"si" tambien 1
    for a, b in (("sunday", "saturday"), ("abc", "yabd"), ("aaaa", "a")):
        assert levenshtein_matriz(a, b)[len(a)][len(b)] == levenshtein_distancia(a, b)


def test_levenshtein_simetria_y_similitud():
    assert levenshtein_distancia("abcdef", "azced") == levenshtein_distancia("azced", "abcdef")
    assert levenshtein_similitud("abc", "abc") == 1.0 and levenshtein_similitud("abc", "xyz") == 0.0
    assert levenshtein_similitud("", "") == 1.0
    assert math.isclose(levenshtein_similitud("kitten", "sitting"), 1 - 3 / 7)


def test_levenshtein_sobre_listas_de_palabras():
    assert levenshtein_distancia(["a", "b", "c"], ["a", "x", "c", "d"]) == 2


# ---- Needleman-Wunsch
def test_needleman_wunsch_ejemplo_clasico():
    # Ejemplo de la literatura: GATTACA / GCATGCU con +1/-1/-1 da puntaje 0
    assert needleman_wunsch_puntaje("GATTACA", "GCATGCU") == 0
    puntaje, a, b, F = needleman_wunsch_alineamiento("GATTACA", "GCATGCU")
    assert puntaje == 0 and F[7][7] == 0 and len(a) == len(b)
    assert [c for c in a if c != "-"] == list("GATTACA") and [c for c in b if c != "-"] == list("GCATGCU")


def test_needleman_wunsch_identicas_y_normalizacion():
    assert needleman_wunsch_puntaje("ABC", "ABC") == 3
    assert needleman_wunsch_similitud("ABC", "ABC") == 1.0
    assert needleman_wunsch_similitud("AAA", "BBB") == pytest.approx((-3 + 6) / (3 + 6))  # (-3 - (-6)) / (3 - (-6))
    assert 0.0 <= needleman_wunsch_normalizado(-999, 3, 3) <= 1.0
    assert needleman_wunsch_puntaje("", "ABC") == -3
    assert needleman_wunsch_matriz("AB", "AB")[2][2] == 2


def test_needleman_wunsch_dos_filas_igual_que_matriz():
    for a, b in (("GATTACA", "GCATGCU"), ("abcdef", "badcfe"), ("aaaa", "aa")):
        assert needleman_wunsch_matriz(a, b)[len(a)][len(b)] == needleman_wunsch_puntaje(a, b)


# ---- TF-IDF
DOCS = [["ai", "education", "ai"], ["education", "learning"], ["learning", "assessment"]]


def test_tfidf_calculo_a_mano():
    vocab = construir_vocabulario(DOCS)
    assert vocab["terminos"] == ["ai", "assessment", "education", "learning"]
    assert vocab["df"] == [1, 1, 2, 2] and vocab["n_docs"] == 3
    idf = calcular_idf(vocab)
    assert idf[0] == pytest.approx(math.log(4 / 2) + 1)           # df=1  -> ln(4/2)+1
    assert idf[2] == pytest.approx(math.log(4 / 3) + 1)           # df=2  -> ln(4/3)+1
    tf = vector_tf(DOCS[0], vocab)
    assert tf == pytest.approx([2 / 3, 0, 1 / 3, 0])
    w = vector_tfidf(DOCS[0], vocab, idf)
    assert w[0] == pytest.approx(2 / 3 * idf[0])


def test_coseno_casos_limite():
    assert coseno_vectores([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert coseno_vectores([1, 0], [0, 1]) == 0.0
    assert coseno_vectores([0, 0], [1, 1]) == 0.0
    assert angulo_grados(coseno_vectores([1, 0], [1, 1])) == pytest.approx(45.0)


def test_coseno_tfidf_documentos_identicos_y_disjuntos():
    vocab = construir_vocabulario(DOCS)
    idf = calcular_idf(vocab)
    v0 = vector_tfidf(DOCS[0], vocab, idf)
    assert coseno_vectores(v0, v0) == pytest.approx(1.0)
    assert coseno_vectores(v0, vector_tfidf(["assessment"], vocab, idf)) == 0.0


# ---- Jaccard
def test_jaccard():
    r = jaccard(["a", "b", "c", "a"], ["b", "c", "d"])
    assert r["similitud"] == pytest.approx(2 / 4) and r["interseccion"] == ["b", "c"] and r["union"] == ["a", "b", "c", "d"]
    assert jaccard([], [])["similitud"] == 1.0
    assert jaccard(["a"], ["b"])["similitud"] == 0.0
    assert jaccard(["a", "b"], ["a", "b"])["similitud"] == 1.0


# ---- Embeddings (formulas)
def test_coseno_y_euclidiana():
    assert coseno([1, 0], [0, 1]) == 0.0 and coseno([2, 0], [5, 0]) == pytest.approx(1.0)
    assert distancia_euclidiana([0, 0], [3, 4]) == pytest.approx(5.0)
    assert similitud_euclidiana_01([1, 1], [1, 1]) == 1.0
    assert similitud_euclidiana_01([0, 0], [3, 4]) == pytest.approx(1 / 6)
    assert similitud_coseno_01([1, 0], [-1, 0]) == 0.0   # negativo se recorta a 0


def test_embeddings_del_corpus_estan_normalizados(corpus):
    assert len(corpus.modelos) >= 2
    for modelo in corpus.modelos.values():
        assert len(modelo["vectores"]) == 20
        for v in modelo["vectores"].values():
            assert len(v) == modelo["dimension"]
            assert math.sqrt(sum(x * x for x in v)) == pytest.approx(1.0, abs=1e-4)


def test_similitud_entre_pares_del_corpus_en_rango(corpus):
    from src.comparacion import similitud_par
    r = similitud_par(corpus, corpus.obtener(2), corpus.obtener(6))
    assert set(r) >= {"levenshtein", "needleman-wunsch", "tfidf-coseno", "jaccard", "emb-glove", "emb-fasttext"}
    for v in r.values():
        assert 0.0 <= v["similitud"] <= 1.0
    # un documento consigo mismo es identico en todos los algoritmos
    mismo = similitud_par(corpus, corpus.obtener(2), corpus.obtener(2))
    for clave, v in mismo.items():
        assert v["similitud"] == pytest.approx(1.0, abs=1e-6), clave
