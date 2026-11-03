import pytest

extraer = pytest.importorskip("extraer_corpus")  # requiere pypdf (solo desarrollo)


def test_localizar_abstract_elsevier():
    texto = "ARTICLE INFO\nKeywords: x\nABSTRACT\nThis is the abstract text that goes on for a while " + "word " * 80 + "end.\n1. Introduction\nbody"
    a = extraer.localizar_abstract(texto, 99)
    assert a.startswith("This is the abstract") and a.rstrip().endswith("end.")


def test_localizar_abstract_mdpi_con_dos_puntos():
    texto = "Title\nAbstract: Generative AI has changed things " + "word " * 80 + "done.\nKeywords: a; b"
    assert extraer.localizar_abstract(texto, 99).startswith("Generative AI")


def test_pdf_sin_abstract_devuelve_none():
    assert extraer.localizar_abstract("Texto sin resumen ni encabezados de ningun tipo.", 99) is None


def test_union_de_guiones_solo_si_la_palabra_existe():
    vocab = {"education", "assessment"}
    texto, unidos, conservados = extraer.unir_guiones("the edu-\ncation of well-\nknown things", vocab)
    assert "education" in texto and "well-known" in texto and unidos == 1 and conservados == 1


def test_reparar_guiones_en_linea_respeta_guiones_suspendidos():
    vocab = {"practitioners", "defined"}
    assert extraer.reparar_guiones_en_linea("pre- and misconceptions", vocab) == "pre- and misconceptions"
    assert extraer.reparar_guiones_en_linea("well- defined", vocab) == "well-defined"
    assert extraer.reparar_guiones_en_linea("practi- tioners", vocab) == "practitioners"


def test_correccion_manual_del_articulo_14():
    t = "within Competence Construct Claims (Child, S., & Shaw, S. 2023). A conceptual approach. Research Matters, 35, 27-40.), each addressing"
    nuevo, motivo = extraer.aplicar_correccion(14, t)
    assert nuevo == "within Competence Construct Claims, each addressing" and motivo
    assert extraer.aplicar_correccion(1, t) == (t, None)


def test_evaluar_calidad_detecta_problemas():
    n, problemas, _ = extraer.evaluar_calidad("corto sin mayuscula", "Titulo", "texto con Titulo", None)
    assert any("corto" in p for p in problemas) and any("mayuscula" in p for p in problemas)
    largo = "Texto " * 100 + "(Smith, 2020) y Keywords."
    _, problemas2, _ = extraer.evaluar_calidad(largo, "Titulo", "Titulo", None)
    assert any("cita" in p for p in problemas2) and any("Keywords" in p for p in problemas2)


def test_reemplazos_documentados():
    nuevo, motivos = extraer.aplicar_reemplazos(6, "we contribute to the researchfield by enabling")
    assert nuevo == "we contribute to the research field by enabling" and len(motivos) == 1
    assert extraer.aplicar_reemplazos(17, "to holisti-cally examine")[0] == "to holistically examine"
    assert extraer.aplicar_reemplazos(1, "researchfield") == ("researchfield", [])
