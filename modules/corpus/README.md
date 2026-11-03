# Corpus y preprocesamiento

- **Proposito:** Convertir los 20 PDFs en un corpus limpio y validado, y mostrar el preprocesamiento paso a paso.
- **Archivos:** scripts/extraer_corpus.py (offline), src/preprocesamiento.py, src/corpus.py, static/modules/corpus/index.html
- **Entradas:** PDFs (solo offline); texto libre en la pagina
- **Salidas:** corpus.json, corpus_limpio.json, reporte_calidad.json; tabla de articulos, abstract y pasos de limpieza
- **Evidencia para sustentar:** Reporte de calidad 20/20 y tests/test_corpus_api.py, tests/test_extraccion.py, tests/test_preprocesamiento.py
