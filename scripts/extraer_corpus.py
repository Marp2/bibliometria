"""Extrae titulo, autores y abstract de los 20 PDFs y genera:
  data/processed/corpus.json           (corpus final)
  data/processed/reporte_calidad.json  (validacion de los 20 abstracts)

Uso:   python scripts/extraer_corpus.py [carpeta_pdfs]
Requiere: pypdf (solo para este script; la app web NO lo necesita).

Nota: este script es herramienta de preparacion de datos (ETL), no un algoritmo
evaluado; por eso puede usar metodos de str (find, replace). Los algoritmos del
proyecto (src/) no los usan.
"""
import json
import os
import sys

from pypdf import PdfReader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_PDFS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "pdfs")
SALIDA = os.path.join(RAIZ, "data", "processed")

LIGADURAS = (("\ufb01", "fi"), ("\ufb02", "fl"), ("\ufb00", "ff"), ("\ufb03", "ffi"), ("\ufb04", "ffl"),
             ("\u00a0", " "), ("\u2009", " "), ("\u200b", ""), ("\u00ad", ""))
MARCAS_INICIO = ("A B S T R A C T", "ABSTRACT", "Abstract")
MARCAS_FIN = ("Keywords", "KEYWORDS", "Key words", "Index Terms", "1. Introduction", "1 Introduction",
              "\n1. Introduction", "INTRODUCTION", "Introduction\n", "\u00a9", "Received:", "Check for")
# PDFs con diseno de dos columnas donde no hay marca limpia de inicio: ancla manual (primeras palabras del abstract)
ANCLAS_INICIO = {7: "The rapid expansion of Learning Analytics"}
# PDFs cuyo abstract no tiene marca de fin ("Keywords"/"Introduction"): ancla con las ultimas palabras
ANCLAS_FIN = {9: "longitudinal research and development efforts."}
# Correcciones manuales documentadas. (id) -> (texto_inicio, texto_fin, motivo)
# Se conserva siempre el texto original en el campo "abstract_original".
CORRECCIONES = {
    14: (" (Child, S., & Shaw, S. 2023)", "40.)",
         "El PDF publicado trae una referencia bibliografica completa pegada dentro del abstract; se elimina."),
}
# Reemplazos puntuales de artefactos de extraccion (ligatura que pego dos palabras, guion de salto de linea sin vocabulario de apoyo)
REEMPLAZOS = {
    6: [("researchfield", "research field", "El PDF pierde el espacio antes de una ligadura: 'researchfield' -> 'research field'.")],
    17: [("holisti-cally", "holistically", "Guion de fin de linea no resuelto por el vocabulario: 'holisti-cally' -> 'holistically'.")],
}
CONJUNCIONES = ("and", "or", "to", "of")
# Longitud razonable de un abstract (palabras) para el reporte de calidad
MIN_PALABRAS, MAX_PALABRAS = 80, 300


def normalizar(texto):
    for a, b in LIGADURAS:
        texto = texto.replace(a, b)
    return texto


def leer_texto(ruta, paginas=2):
    lector = PdfReader(ruta)
    partes = []
    for i in range(min(paginas, len(lector.pages))):
        partes.append(normalizar(lector.pages[i].extract_text() or ""))
    return "\n".join(partes)


def vocabulario_global(textos):
    """Palabras que aparecen enteras (sin corte de linea) en cualquier PDF; sirve para decidir si 'edu-\\ncation' se une."""
    vocab = set()
    for t in textos:
        for linea in t.split("\n"):
            for w in linea.replace("-", " ").split():
                w = "".join(c for c in w.lower() if c.isalpha())
                if len(w) > 2:
                    vocab.add(w)
    return vocab


def unir_guiones(texto, vocab):
    """Une palabras cortadas por guion de fin de linea solo si la palabra unida existe en el vocabulario."""
    lineas = texto.split("\n")
    salida = []
    unidos = 0
    conservados = 0
    i = 0
    while i < len(lineas):
        linea = lineas[i].rstrip()
        if i + 1 < len(lineas) and linea.endswith("-") and len(linea) > 1:
            sig = lineas[i + 1].lstrip()
            ant = linea[:-1].rstrip().split(" ")[-1] if linea[:-1].strip() else ""
            pri = sig.split(" ")[0] if sig else ""
            a = "".join(c for c in ant.lower() if c.isalpha())
            p = "".join(c for c in pri.lower() if c.isalpha())
            if a and p and (a + p) in vocab and pri[:1].islower():
                # unir: quitar guion y salto
                resto = linea[:-1].rstrip()
                lineas[i + 1] = resto + sig
                unidos += 1
                i += 1
                continue
            conservados += 1
            lineas[i + 1] = linea + sig
            i += 1
            continue
        salida.append(linea)
        i += 1
    return "\n".join(salida), unidos, conservados


def localizar_abstract(texto, id_doc):
    if id_doc in ANCLAS_INICIO:
        ini = texto.find(ANCLAS_INICIO[id_doc])
    else:
        candidatos = [texto.find(m) + len(m) for m in MARCAS_INICIO if texto.find(m) >= 0]
        ini = min(candidatos) if candidatos else -1
    if ini < 0:
        return None
    while ini < len(texto) and texto[ini] in " :\n.-\u2014":
        ini += 1
    if id_doc in ANCLAS_FIN:
        pos = texto.find(ANCLAS_FIN[id_doc], ini)
        if pos >= 0:
            return texto[ini:pos + len(ANCLAS_FIN[id_doc])]
    fines = [texto.find(m, ini + 300) for m in MARCAS_FIN if texto.find(m, ini + 300) >= 0]
    fin = min(fines) if fines else min(len(texto), ini + 2500)
    return texto[ini:fin]


def limpiar_abstract(bruto, vocab):
    t = bruto.replace("\n", " ")
    while "  " in t:
        t = t.replace("  ", " ")
    t = t.replace(" \u2019", "\u2019").replace(" '", "'") if False else t.replace(" \u2019", "\u2019")
    return reparar_guiones_en_linea(t.strip(), vocab)


def reparar_guiones_en_linea(t, vocab):
    """'well- defined' -> 'well-defined'; 'edu- cation' -> 'education' (si la palabra unida existe en el vocabulario).
    Respeta guiones suspendidos legitimos como 'pre- and misconceptions'."""
    palabras_ = t.split(" ")
    salida = []
    i = 0
    while i < len(palabras_):
        w = palabras_[i]
        if (len(w) > 1 and w.endswith("-") and w[-2].isalpha() and i + 1 < len(palabras_)
                and palabras_[i + 1][:1].islower() and palabras_[i + 1] not in CONJUNCIONES):
            sig = palabras_[i + 1]
            a = "".join(c for c in w.lower() if c.isalpha())
            p = "".join(c for c in sig.lower() if c.isalpha())
            if (a + p) in vocab:
                salida.append(w[:-1] + sig)
            else:
                salida.append(w + sig)
            i += 2
            continue
        salida.append(w)
        i += 1
    return " ".join(salida)


def aplicar_correccion(id_doc, t):
    if id_doc not in CORRECCIONES:
        return t, None
    ini_txt, fin_txt, motivo = CORRECCIONES[id_doc]
    a = t.find(ini_txt)
    b = t.find(fin_txt, a + 1)
    if a < 0 or b < 0:
        return t, None
    return t[:a] + t[b + len(fin_txt):], motivo


def aplicar_reemplazos(id_doc, t):
    """Aplica los reemplazos documentados. Devuelve (texto, lista_de_motivos)."""
    motivos = []
    for viejo, nuevo, motivo in REEMPLAZOS.get(id_doc, []):
        k = t.find(viejo)
        if k >= 0:
            t = t[:k] + nuevo + t[k + len(viejo):]
            motivos.append(motivo)
    return t, motivos


def tiene_cita(t):
    """Detecta '(Autor, 2021)' o 'et al.' dentro de parentesis."""
    pos = t.find("(")
    while pos >= 0:
        cierre = t.find(")", pos)
        if cierre < 0:
            break
        seg = t[pos + 1:cierre]
        for anio in range(1990, 2027):
            k = seg.find(", %d" % anio)
            if k > 0 and seg[k - 1].isalpha():
                return True
            if seg.find(" %d" % anio) > 0 and seg[:1].isupper() and seg.find("&") >= 0:
                return True
        pos = t.find("(", cierre)
    return False


def solo_alfanum(s):
    return "".join(c.lower() for c in s if c.isalnum())


def palabras(t):
    return [w for w in t.split(" ") if w]


def evaluar_calidad(a, titulo, texto_p1, java_ref):
    problemas = []
    n = len(palabras(a))
    if n < MIN_PALABRAS:
        problemas.append("abstract demasiado corto (%d palabras)" % n)
    if n > MAX_PALABRAS:
        problemas.append("abstract demasiado largo (%d palabras)" % n)
    if not a[:1].isupper():
        problemas.append("no inicia con mayuscula")
    if a.rstrip()[-1:] not in ".!?":
        problemas.append("no termina en punto")
    for marca in ("et al.", "doi.org", "http", "\u00a9", "Keywords", "KEYWORDS", "Received", "Corresponding"):
        if a.find(marca) >= 0:
            problemas.append("contiene residuo: '%s'" % marca)
    if tiene_cita(a):
        problemas.append("posible cita bibliografica dentro del abstract")
    avisos = []
    k = a.find("- ")
    while k >= 0:
        if k > 0 and a[k - 1].isalpha() and a[k + 2:k + 3].islower():
            sig = a[k + 2:].split(" ")[0]
            if sig not in CONJUNCIONES:
                problemas.append("posible guion de fin de linea: '%s'" % a[max(0, k - 10):k + 12])
        k = a.find("- ", k + 1)
    raros = [c for c in a if ord(c) > 127 and c not in "\u2013\u2014\u2018\u2019\u201c\u201d\u2026\u00e9\u00ed\u00f3\u00e1\u00fa\u00f1\u00f6\u00fc\u00e4"]
    if raros:
        problemas.append("caracteres no esperados: %s" % "".join(sorted(set(raros)))[:20])
    if solo_alfanum(titulo) not in solo_alfanum(texto_p1):
        problemas.append("el titulo verificado no aparece textual en la pagina 1")
    concordancia = None
    if java_ref:
        a_set, b_set = set(w.lower().strip(".,;:()") for w in palabras(a)), set(w.lower().strip(".,;:()") for w in palabras(java_ref))
        inter, uni = 0, len(a_set)
        for w in b_set:
            if w in a_set:
                inter += 1
            else:
                uni += 1
        concordancia = round(inter / uni, 3) if uni else 0
        if concordancia < 0.9:
            problemas.append("difiere de la extraccion Java de referencia (Jaccard %.2f)" % concordancia)
    return n, problemas, concordancia


def cargar_java(id_doc):
    ruta = os.path.join(RAIZ, "data", "referencia_java", "%d.txt" % id_doc)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        partes = f.read().split("\n", 2)
    return partes[2].strip().replace("\n", " ") if len(partes) > 2 else None


def main():
    with open(os.path.join(RAIZ, "data", "metadata_verificada.json"), encoding="utf-8") as f:
        meta = json.load(f)
    archivos = {}
    for nombre in os.listdir(CARPETA_PDFS):
        if nombre.lower().endswith(".pdf"):
            num = ""
            for c in nombre:
                if c.isdigit():
                    num += c
                else:
                    break
            if num:
                archivos[int(num)] = nombre
    if len(archivos) != 20:
        print("ADVERTENCIA: se esperaban 20 PDFs numerados y hay %d en %s" % (len(archivos), CARPETA_PDFS))
    textos = {i: leer_texto(os.path.join(CARPETA_PDFS, archivos[i])) for i in sorted(archivos)}
    vocab = vocabulario_global(textos.values())
    corpus, reporte = [], []
    for i in sorted(archivos):
        texto = textos[i]
        pagina1 = normalizar(PdfReader(os.path.join(CARPETA_PDFS, archivos[i])).pages[0].extract_text() or "")
        texto_unido, unidos, conservados = unir_guiones(texto, vocab)
        bruto = localizar_abstract(texto_unido, i)
        m = meta[str(i)]
        if bruto is None:
            reporte.append({"id": i, "archivo": archivos[i], "estado": "ERROR", "problemas": ["no se encontro abstract"]})
            continue
        abstract_original = limpiar_abstract(bruto, vocab)
        abstract, motivo = aplicar_correccion(i, abstract_original)
        abstract, motivos_extra = aplicar_reemplazos(i, abstract)
        if motivos_extra:
            motivo = " ".join([m for m in [motivo] + motivos_extra if m])
        n, problemas, concord = evaluar_calidad(abstract, m["titulo"], pagina1, None if motivo else cargar_java(i))
        registro = {"id": i, "archivo": archivos[i], "titulo": m["titulo"], "autores": m["autores"],
                    "abstract": abstract}
        if motivo:
            registro["abstract_original"] = abstract_original
            registro["correccion_manual"] = motivo
        corpus.append(registro)
        reporte.append({"id": i, "archivo": archivos[i], "titulo": m["titulo"], "palabras": n,
                        "caracteres": len(abstract), "guiones_unidos": unidos, "guiones_conservados": conservados,
                        "correccion_manual": motivo, "concordancia_java": concord, "estado": "OK" if not problemas else "REVISAR",
                        "problemas": problemas})
    os.makedirs(SALIDA, exist_ok=True)
    with open(os.path.join(SALIDA, "corpus.json"), "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)
    with open(os.path.join(SALIDA, "reporte_calidad.json"), "w", encoding="utf-8") as f:
        json.dump({"total_pdfs": len(archivos), "total_extraidos": len(corpus),
                   "ok": sum(1 for r in reporte if r["estado"] == "OK"), "detalle": reporte}, f, ensure_ascii=False, indent=2)
    print("%d/%d abstracts extraidos" % (len(corpus), len(archivos)))
    for r in reporte:
        print(r["id"], r["estado"], r.get("palabras"), "|", "; ".join(r["problemas"]) if r["problemas"] else "")


if __name__ == "__main__":
    main()
