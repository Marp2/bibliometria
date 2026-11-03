"""Genera la documentacion a partir de docs/evidencias/evidencias.json (que a su vez sale de ejecutar el codigo).

Uso:  python scripts/generar_documentos.py
Salidas: docs/DOCUMENTO_TECNICO_FINAL.md, DOCUMENTACION_TECNICA.md, GUIA_SUSTENTACION_PROYECTO.md,
         HOJA_DE_RUTA_COMPLETA.md y los diagramas docs/figuras/arquitectura.png y flujo_datos.png
Conversion opcional a Word/PDF (requiere pandoc):  cd docs && pandoc DOCUMENTO_TECNICO_FINAL.md -o DOCUMENTO_TECNICO_FINAL.docx
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

import doc_apoyo  # noqa: E402
import doc_final  # noqa: E402

DOCS = os.path.join(RAIZ, "docs")
FIG = os.path.join(DOCS, "figuras")


def caja(ax, x, y, w, h, texto, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03", facecolor=color, edgecolor="#1e293b", linewidth=1.2))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=8.5, wrap=True)


def flecha(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12, color="#334155", linewidth=1.2))


def diagrama_componentes():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    caja(ax, 0.2, 4.6, 2.6, 1.0, "Navegador\n5 paginas HTML + app.js", "#dbeafe")
    caja(ax, 3.6, 4.6, 2.8, 1.0, "Flask (src/api.py)\nendpoints JSON y PNG", "#bfdbfe")
    caja(ax, 7.2, 4.6, 2.6, 1.0, "Render\ngunicorn (1 worker)", "#e2e8f0")
    caja(ax, 0.2, 2.8, 2.6, 1.1, "Req. 1\nsimilitud_clasica\nsimilitud_embeddings\ncomparacion", "#dcfce7")
    caja(ax, 3.6, 2.8, 2.8, 1.1, "Req. 2\nclustering\n(+ visualizacion)", "#fef9c3")
    caja(ax, 7.2, 2.8, 2.6, 1.1, "Req. 3\npatrones\nbenchmark_patrones", "#fee2e2")
    caja(ax, 0.2, 1.0, 4.2, 1.0, "Nucleo comun: preprocesamiento + estructuras_datos\n(lista, pila, tabla hash, conjunto, merge sort)", "#ede9fe")
    caja(ax, 5.2, 1.0, 4.6, 1.0, "Datos (data/processed): corpus.json, corpus_limpio.json,\nreporte_calidad.json, embeddings_glove/fasttext.json", "#fce7f3")
    caja(ax, 0.2, 0.0, 9.6, 0.6, "Offline (fuera del servidor): scripts/extraer_corpus.py (pypdf) y scripts/generar_embeddings.py (modelos preentrenados)", "#f1f5f9")
    for (x1, y1, x2, y2) in ((2.8, 5.1, 3.6, 5.1), (6.4, 5.1, 7.2, 5.1), (4.9, 4.6, 1.5, 3.9), (5.0, 4.6, 5.0, 3.9), (5.6, 4.6, 8.5, 3.9),
                             (1.5, 2.8, 1.5, 2.0), (5.0, 2.8, 3.0, 2.0), (8.5, 2.8, 3.8, 2.0), (6.0, 1.0, 6.0, 0.6)):
        flecha(ax, x1, y1, x2, y2)
    ax.set_title("Diagrama de componentes", fontsize=11)
    fig.savefig(os.path.join(FIG, "arquitectura.png"), dpi=130, bbox_inches="tight")
    plt.close(fig)


def diagrama_flujo():
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 3.6)
    ax.axis("off")
    pasos = [("20 PDFs", "#f1f5f9"), ("extraer_corpus.py\ntitulo, autores, abstract", "#dbeafe"), ("corpus.json\n+ reporte_calidad", "#fce7f3"),
             ("preprocesamiento\n(minusculas, tokens,\nstopwords, stemming)", "#ede9fe"), ("TF-IDF / texto limpio /\nembeddings (offline)", "#dcfce7"),
             ("Algoritmos propios\nReq. 1, 2, 3", "#fef9c3"), ("API + graficas\n+ web", "#fee2e2")]
    x = 0.1
    for i, (t, c) in enumerate(pasos):
        caja(ax, x, 1.2, 1.35, 1.3, t, c)
        if i < len(pasos) - 1:
            flecha(ax, x + 1.35, 1.85, x + 1.55, 1.85)
        x += 1.55
    ax.text(0.8, 0.7, "OFFLINE (una vez)", ha="center", fontsize=8, color="#475569")
    ax.text(8.8, 0.7, "ONLINE (servidor)", ha="center", fontsize=8, color="#475569")
    ax.plot([0.1, 4.8], [0.95, 0.95], color="#94a3b8")
    ax.plot([6.3, 10.9], [0.95, 0.95], color="#94a3b8")
    ax.set_title("Flujo de datos", fontsize=11)
    fig.savefig(os.path.join(FIG, "flujo_datos.png"), dpi=130, bbox_inches="tight")
    plt.close(fig)


def main():
    with open(os.path.join(DOCS, "evidencias", "evidencias.json"), encoding="utf-8") as fh:
        ev = json.load(fh)
    os.makedirs(FIG, exist_ok=True)
    diagrama_componentes()
    diagrama_flujo()
    salidas = {"DOCUMENTO_TECNICO_FINAL.md": doc_final.construir(ev), "DOCUMENTACION_TECNICA.md": doc_apoyo.documentacion_tecnica(ev),
               "GUIA_SUSTENTACION_PROYECTO.md": doc_apoyo.guia(ev), "HOJA_DE_RUTA_COMPLETA.md": doc_apoyo.hoja_de_ruta(ev)}
    for nombre, texto in salidas.items():
        with open(os.path.join(DOCS, nombre), "w", encoding="utf-8") as fh:
            fh.write(texto)
        print("escrito docs/%s (%d caracteres)" % (nombre, len(texto)))


if __name__ == "__main__":
    main()
