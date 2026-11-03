from src.preprocesamiento import (
    a_minusculas, aplicar_stemming, limpiar_signos, preprocesar, quitar_stopwords, quitar_tildes, stem_simple, texto_normalizado,
    tokenizar,
)


def test_minusculas_y_tildes():
    assert a_minusculas("Education AI ÁÉÑ") == "education ai áéñ"
    assert quitar_tildes("educación análisis ñandú") == "educacion analisis nandu"


def test_limpiar_signos_digitos_y_guiones():
    assert tokenizar(limpiar_signos("ai-driven (2023) learners' test!")) == ["ai", "driven", "learners", "test"]


def test_tokenizar_espacios_multiples_y_vacio():
    assert tokenizar("  a   b  ") == ["a", "b"]
    assert tokenizar("") == [] and tokenizar("    ") == []


def test_stopwords_en_es_y_longitud_minima():
    toks = ["the", "learners", "de", "la", "educacion", "ai", "x", "of"]
    assert quitar_stopwords(toks) == ["learners", "educacion", "ai"]  # 'ai' se conserva (2 letras, no es stopword)


def test_stemming_reglas():
    esperados = {"education": "educate", "educational": "educate", "learning": "learn", "studies": "study",
                 "models": "model", "analysis": "analysis", "ai": "ai", "this": "this"}
    for palabra, stem in esperados.items():
        assert stem_simple(palabra) == stem, palabra
    assert aplicar_stemming(["models", "model"]) == ["model", "model"]


def test_pipeline_completo():
    r = preprocesar("The Learners' Education: AI-driven assessments (2023).")
    assert r["tokens_sin_stopwords"] == ["learners", "education", "ai", "driven", "assessments"]
    assert r["tokens_finales"] == ["learner", "educate", "ai", "driven", "assessment"]
    assert r["texto_limpio"] == "learners education ai driven assessments"
    assert texto_normalizado("A  b,\nC") == "a b c"


def test_texto_vacio_o_solo_signos():
    assert preprocesar("")["tokens_finales"] == []
    assert preprocesar("!!! 123 ...")["tokens_finales"] == []
