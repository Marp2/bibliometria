# Analisis de algoritmos en el contexto de la bibliometria

Proyecto final de **Analisis de Algoritmos** (Universidad del Quindio, 2026-2).
Dominio: inteligencia artificial generativa / IA en educacion. Corpus: 20 articulos cientificos; se procesa **solo el abstract**.

Integrantes: Cristhian Camilo Lopez Grajales, Mariana Pineda Montenegro y Camila Hernandez Peña.

**Aplicacion desplegada:** `https://bibliometria-algoritmos-gp0j.onrender.com/ui/corpus` 

## Que incluye

| Requerimiento | Pagina | Codigo |
|---|---|---|
| Corpus y preprocesamiento | `/ui/corpus` | `src/preprocesamiento.py`, `scripts/extraer_corpus.py` |
| 1. Similitud textual: Levenshtein, Needleman-Wunsch, coseno TF-IDF, Jaccard + 2 embeddings (GloVe, fastText) | `/ui/similarity` | `src/similitud_clasica.py`, `src/similitud_embeddings.py` |
| 2. Clustering jerarquico: Single, Complete, Average + dendrogramas | `/ui/clustering` | `src/clustering.py` |
| 3. Busqueda de patrones: KMP, Boyer-Moore, Rabin-Karp | `/ui/patterns` | `src/patrones.py` |
| 4. Despliegue y documentacion | `/ui/docs` | `docs/` |

**Regla de oro:** los algoritmos estan escritos desde cero con listas y bucles. Sin scipy, sklearn, numpy ni pandas en `src/`
(scipy solo aparece en las pruebas, de forma opcional, para verificar). Los datos ya vienen calculados en `data/processed/`.

## Ejecutar en local (Windows / PowerShell)

Requiere Python 3.10 o superior.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -q
python api.py
```

Abra http://127.0.0.1:8000/ . (Si PowerShell bloquea el script de activacion: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.)

En macOS / Linux: `python3 -m venv .venv && source .venv/bin/activate`, y los mismos comandos `pip`, `pytest` y `python api.py`.

Solo para ejecutar la app basta `pip install -r requirements.txt` (Flask, matplotlib, gunicorn).

## Desplegar en Render (plan gratuito)

1. Suba esta carpeta a un repositorio de GitHub (`git init`, `git add .`, `git commit -m "proyecto"`, `git remote add origin <url>`, `git push -u origin main`). `pdfs/` y `data/modelos_cache/` ya estan en `.gitignore`.
2. En https://render.com: **New > Web Service** y conecte el repositorio (o **New > Blueprint** para usar `render.yaml`).
3. Si lo hace manualmente: *Runtime* Python 3, *Build Command* `pip install -r requirements.txt`, *Start Command* `gunicorn src.api:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`, *Plan* Free.
4. Cuando termine, abra `<url>/health`: debe responder `{"status":"ok","articulos":20,...}`.
5. Copie la URL publica en este README y en `docs/` (reemplazando `ENLACE_PUBLICO_DE_RENDER`) y vuelva a ejecutar `python scripts/generar_documentos.py`.

Variables de entorno opcionales: `BIBLIO_DATA_DIR` (carpeta `data`), `BIBLIO_REPORTS_DIR`; si la carpeta no se puede escribir, se usa una temporal.
El plan gratuito "duerme" tras inactividad: la primera consulta puede tardar. Comparar 6 articulos (15 pares) es el calculo mas pesado.

## Regenerar datos y documentos (opcional)

```powershell
pip install -r requirements-dev.txt
# 1) Corpus (requiere los 20 PDFs en .\pdfs, nombrados 1__..., 2__..., ... 20__...)
python scripts/extraer_corpus.py
# 2) Embeddings (descarga ~1.4 GB la primera vez; ya incluidos en data/processed)
python scripts/generar_embeddings.py                # glove + fasttext
python scripts/generar_embeddings.py sbert          # OPCIONAL (no ejecutado en el trabajo): pip install sentence-transformers
# 3) Evidencias reales (corre los algoritmos y mide tiempos, ~1-2 min) y documentos
python scripts/generar_evidencias.py
python scripts/generar_documentos.py
```

## Estructura

```text
api.py  Procfile  render.yaml  requirements.txt  requirements-dev.txt
src/       estructuras_datos, preprocesamiento, similitud_clasica, similitud_embeddings, comparacion,
           clustering, patrones, benchmark_patrones, visualizacion, corpus, docs_algoritmos, paths, api
scripts/   extraer_corpus, generar_embeddings, generar_evidencias, generar_documentos
data/processed/   corpus.json, corpus_limpio.json, reporte_calidad.json, embeddings_*.json
static/    styles.css, app.js, modules/<modulo>/index.html
modules/   README por modulo
tests/     pytest
docs/      DOCUMENTO_TECNICO_FINAL (.md .docx .pdf), DOCUMENTACION_TECNICA, GUIA_SUSTENTACION_PROYECTO,
           HOJA_DE_RUTA_COMPLETA, figuras/, evidencias/
```

## Documentacion

- `docs/DOCUMENTO_TECNICO_FINAL.docx` / `.pdf` / `.md`: documento tecnico (arquitectura, casos de estudio, resultados, IA declarada).
- `docs/GUIA_SUSTENTACION_PROYECTO.md`: preguntas tipicas y respuestas cortas.
- `docs/HOJA_DE_RUTA_COMPLETA.md`: lista de verificacion contra el enunciado y pendientes del grupo.
