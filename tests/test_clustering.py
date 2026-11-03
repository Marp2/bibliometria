import math

import pytest

from src.clustering import (
    agrupar, comparar_criterios, correlacion_cofenetica, cortar_en_k, distancias_cofeneticas, evaluar, matriz_distancias,
    orden_hojas, pearson, silueta,
)

# Cuatro puntos en una recta: 0, 1, 5, 7  -> distancias absolutas
PUNTOS = [0.0, 1.0, 5.0, 7.0]
D4 = [[abs(a - b) for b in PUNTOS] for a in PUNTOS]


def alturas(h):
    return [f["distancia"] for f in h]


def test_single_a_mano():
    h = agrupar(D4, "single")
    assert alturas(h) == [1.0, 2.0, 4.0]          # (0,1)=1 ; (5,7)=2 ; unir grupos = min(5,7,4,6)=4
    assert (h[0]["a"], h[0]["b"]) == (0, 1) and h[0]["tamano"] == 2 and h[-1]["tamano"] == 4


def test_complete_a_mano():
    assert alturas(agrupar(D4, "complete")) == [1.0, 2.0, 7.0]   # max(5,7,4,6)=7


def test_average_a_mano():
    assert alturas(agrupar(D4, "average")) == [1.0, 2.0, pytest.approx((5 + 7 + 4 + 6) / 4)]  # 5.5


def test_criterio_invalido_y_pocos_documentos():
    with pytest.raises(ValueError):
        agrupar(D4, "ward")
    with pytest.raises(ValueError):
        agrupar([[0.0]], "single")


def test_cofenetica_y_ccc():
    h = agrupar(D4, "single")
    C = distancias_cofeneticas(h, 4)
    assert C[0][1] == 1.0 and C[2][3] == 2.0 and C[0][2] == 4.0 and C[1][3] == 4.0
    assert pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0) and pearson([1, 1, 1], [1, 2, 3]) == 0.0
    assert -1.0 <= correlacion_cofenetica(D4, h) <= 1.0


def test_cortar_en_k():
    h = agrupar(D4, "single")
    assert cortar_en_k(h, 4, 1) == [0, 0, 0, 0]
    e2 = cortar_en_k(h, 4, 2)
    assert e2[0] == e2[1] and e2[2] == e2[3] and e2[0] != e2[2]
    assert len(set(cortar_en_k(h, 4, 4))) == 4
    with pytest.raises(ValueError):
        cortar_en_k(h, 4, 5)


def test_silueta_grupos_claros():
    s = silueta(D4, [0, 0, 1, 1])
    # i=0: a=1, b=(5+7)/2=6 -> 5/6 ; i=1: a=1, b=(4+6)/2=5 -> 4/5 ; i=2: a=2, b=(5+4)/2=4.5 -> 2.5/4.5 ; i=3: a=2, b=(7+6)/2=6.5 -> 4.5/6.5
    esperado = (5 / 6 + 4 / 5 + 2.5 / 4.5 + 4.5 / 6.5) / 4
    assert s == pytest.approx(esperado)
    assert silueta(D4, [0, 0, 0, 0]) == 0.0


def test_orden_de_hojas_contiene_todos():
    h = agrupar(D4, "average")
    assert sorted(orden_hojas(h, 4)) == [0, 1, 2, 3]


def test_matriz_distancias_simetrica_y_diagonal_cero():
    D = matriz_distancias([[1, 0], [1, 1], [0, 1]])
    assert D[0][0] == 0 and D[0][1] == pytest.approx(D[1][0]) and D[0][2] == pytest.approx(1.0)


def test_contra_scipy_solo_en_pruebas():
    """scipy se usa UNICAMENTE aqui para verificar; nunca en src/."""
    scipy_h = pytest.importorskip("scipy.cluster.hierarchy")
    spatial = pytest.importorskip("scipy.spatial.distance")
    import random
    random.seed(7)
    pts = [[random.random() for _ in range(5)] for _ in range(15)]
    D = [[math.dist(a, b) for b in pts] for a in pts]
    condensada = spatial.squareform(D, checks=False)
    for criterio, metodo in (("single", "single"), ("complete", "complete"), ("average", "average")):
        mio = agrupar(D, criterio)
        Z = scipy_h.linkage(condensada, method=metodo)
        assert alturas(mio) == pytest.approx(list(Z[:, 2]), abs=1e-9), criterio
        ccc_scipy, _ = scipy_h.cophenet(Z, condensada)
        assert correlacion_cofenetica(D, mio) == pytest.approx(ccc_scipy, abs=1e-9), criterio


def test_corpus_clustering(corpus):
    D = matriz_distancias([d["tfidf"] for d in corpus.documentos])
    assert len(D) == 20
    comp = comparar_criterios(D)
    assert comp["mejor"] in ("single", "complete", "average") and len(comp["resultados"]) == 3
    for r in comp["resultados"]:
        assert len(r["historial"]) == 19 and -1.0 <= r["ccc"] <= 1.0
        alt = [f["distancia"] for f in r["historial"]]
        if r["criterio"] != "centroid":
            assert alt == sorted(alt), "alturas monotonas no decrecientes (propiedad de single/complete/average)"
    assert evaluar(D, "average")["mejor_k"] >= 2
