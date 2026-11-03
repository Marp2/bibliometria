import json
import os

import pytest

from src.corpus import Corpus, ErrorCorpus

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---- corpus
def test_corpus_tiene_20_articulos_completos(corpus):
    assert len(corpus.documentos) == 20 and corpus.ids() == list(range(1, 21))
    for d in corpus.documentos:
        palabras = len(d["abstract"].split())
        assert 100 <= palabras <= 300, (d["id"], palabras)
        assert d["titulo"].strip() != "" and len(d["autores"]) >= 1
        assert d["abstract"][0].isupper() and d["abstract"].rstrip()[-1] in ".!?"


def test_reporte_de_calidad_sin_errores():
    with open(os.path.join(RAIZ, "data", "processed", "reporte_calidad.json"), encoding="utf-8") as f:
        r = json.load(f)
    assert r["total_pdfs"] == 20 and r["total_extraidos"] == 20 and r["ok"] == 20


def test_articulo_14_conserva_el_original_y_la_correccion(corpus):
    with open(os.path.join(RAIZ, "data", "processed", "corpus.json"), encoding="utf-8") as f:
        d14 = [d for d in json.load(f) if d["id"] == 14][0]
    assert "Child, S." in d14["abstract_original"] and "Child, S." not in d14["abstract"]
    assert "correccion_manual" in d14


def test_articulo_inexistente_o_invalido(corpus):
    for malo in (0, 21, 999, "abc", None, -3):
        with pytest.raises(ErrorCorpus):
            corpus.obtener(malo)


def test_corpus_faltante(tmp_path):
    with pytest.raises(Exception):
        Corpus(str(tmp_path / "no_existe.json"))


def test_corpus_vacio(tmp_path):
    ruta = tmp_path / "vacio.json"
    ruta.write_text("[]", encoding="utf-8")
    with pytest.raises(ErrorCorpus):
        Corpus(str(ruta))


def test_vocabulario_e_idf(corpus):
    assert len(corpus.vocab["terminos"]) > 500
    assert all(v > 0 for v in corpus.idf)


# ---- API
def test_health(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200 and r.get_json()["articulos"] == 20


def test_paginas(cliente):
    for m in ("corpus", "similarity", "clustering", "patterns", "docs"):
        assert cliente.get("/ui/" + m).status_code == 200
    assert cliente.get("/ui/otro").status_code == 404
    assert cliente.get("/").status_code == 302


def test_api_corpus(cliente):
    assert len(cliente.get("/api/corpus").get_json()) == 20
    assert cliente.get("/api/corpus/7").get_json()["id"] == 7
    r = cliente.get("/api/corpus/99")
    assert r.status_code == 404 and "no existe" in r.get_json()["detail"]


def test_api_similitud_ok_y_errores(cliente):
    r = cliente.post("/api/similarity", json={"ids": [2, 6, 14]})
    assert r.status_code == 200
    datos = r.get_json()
    assert len(datos["pares"]) == 3 and len(datos["algoritmos"]) == 6
    for p in datos["pares"]:
        for v in p["resultados"].values():
            assert 0.0 <= v["similitud"] <= 1.0
    assert cliente.post("/api/similarity", json={"ids": [1]}).status_code == 400          # menos de 2
    assert cliente.post("/api/similarity", json={"ids": [3, 3]}).status_code == 400       # repetidos -> 1 unico
    assert cliente.post("/api/similarity", json={"ids": [1, 99]}).status_code == 404      # inexistente
    assert cliente.post("/api/similarity", json={"ids": list(range(1, 9))}).status_code == 400  # mas de 6
    assert cliente.post("/api/similarity", json={}).status_code == 400
    assert cliente.post("/api/similarity", data="no json").status_code == 400


def test_api_detalle(cliente):
    assert cliente.get("/api/similarity/detalle?a=2&b=6").status_code == 200
    assert cliente.get("/api/similarity/detalle?a=2&b=2").status_code == 400
    assert cliente.get("/api/similarity/detalle?a=x&b=2").status_code == 400
    assert cliente.get("/api/similarity/detalle?a=2&b=77").status_code == 404


def test_api_clustering(cliente):
    r = cliente.get("/api/clustering/comparar").get_json()
    assert r["mejor"] in ("single", "complete", "average") and len(r["criterios"]) == 3
    assert cliente.get("/api/clustering/grupos?criterio=average&k=4").status_code == 200
    assert cliente.get("/api/clustering/grupos?criterio=ward&k=4").status_code == 400
    assert cliente.get("/api/clustering/grupos?criterio=average&k=99").status_code == 400
    for c in ("single", "complete", "average"):
        img = cliente.get("/plot/dendrogram.png?criterio=%s&k=3" % c)
        assert img.status_code == 200 and img.mimetype == "image/png" and img.data[:4] == b"\x89PNG"
    assert cliente.get("/plot/dendrogram.png?criterio=zzz").status_code == 400


def test_api_patrones(cliente):
    r = cliente.get("/api/patterns/search?patron=assessment&algoritmo=todos").get_json()
    assert r["total"] > 0 and r["comparacion"]["coinciden"] is True
    assert cliente.get("/api/patterns/search?patron=&algoritmo=kmp").status_code == 400
    assert cliente.get("/api/patterns/search?patron=%20%20").status_code == 400
    assert cliente.get("/api/patterns/search?patron=x&algoritmo=otro").status_code == 400
    larga = "a" * 1000
    assert cliente.get("/api/patterns/search?patron=" + larga).status_code == 400
    sin = cliente.get("/api/patterns/search?patron=qqqqqqqqqqqqqqqqqq").get_json()
    assert sin["total"] == 0 and sin["resultados"] == []
    img = cliente.get("/plot/patterns.png?patron=assessment&doc=16&algoritmo=kmp")
    assert img.status_code == 200 and img.data[:4] == b"\x89PNG"
    assert cliente.get("/plot/patterns.png?patron=assessment&doc=99&algoritmo=kmp").status_code == 404


def test_api_benchmark(cliente):
    r = cliente.get("/api/patterns/benchmark?patron=learning&repeticiones=1").get_json()
    assert set(r["corpus"]) == {"kmp", "boyer-moore", "rabin-karp"}
    ocu = {a: r["corpus"][a]["ocurrencias"] for a in r["corpus"]}
    assert len(set(ocu.values())) == 1


def test_preprocesar_endpoint(cliente):
    r = cliente.post("/api/preprocesar", json={"texto": "AI-driven Education", "stemming": True})
    assert r.get_json()["tokens_finales"] == ["ai", "driven", "educate"]
    assert cliente.post("/api/preprocesar", json={"texto": "   "}).status_code == 400
    assert cliente.post("/api/preprocesar", json={"texto": "x" * 30000}).status_code == 400


def test_informe_inexistente_o_formato_invalido(cliente):
    assert cliente.get("/report/exe").status_code == 404
