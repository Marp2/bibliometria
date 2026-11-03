# Hoja de ruta y lista de verificacion

## 1. Estado por fase

| Fase | Contenido | Estado |
|------------|-----------------------------------------------------------------|------------------------------------------------------------------|
| 0 | Lectura del proyecto anterior, plan y estructura | Completa |
| 1 | Extraccion de 20 abstracts, reporte de calidad y preprocesamiento | Completa (20/20 validados) |
| 2 | Requerimiento 1: codigo, pruebas, pagina web y documentacion | Completa |
| 3 | Requerimiento 2 | Completa |
| 4 | Requerimiento 3 | Completa |
| 5 | Integracion, interfaz final y archivos de despliegue | Completa; **el despliegue en Render lo realiza el grupo** (README) |
| 6 | Documento tecnico, guia de sustentacion y revision | Completa (borradores: el grupo debe revisarlos) |


## 2. Verificacion contra el enunciado

| Requisito del enunciado | Evidencia | Estado |
|----------------------------------------------------------------------|-----------------------------------------------------|----------------------------------------------------------------------|
| 20 PDFs: titulo, autores y abstract; foco en el abstract | `data/processed/corpus.json`, `reporte_calidad.json` | Cumple |
| R1: seleccion dinamica de 2 o mas articulos | `/ui/similarity` (2 a 6) | Cumple |
| R1: 4 algoritmos clasicos desde cero | `src/similitud_clasica.py` | Cumple |
| R1: 2 modelos de IA con embeddings, similitud coseno/euclidiana | GloVe y fastText; `src/similitud_embeddings.py` | Cumple (modelos de palabras promediados) |
| R1: caso de estudio, paso a paso y analisis critico | Documento tecnico, seccion 4 | Cumple |
| R2: 3 criterios de enlace desde cero, historial, dendrogramas propios | `src/clustering.py`, `docs/figuras/dendrograma_*.png` | Cumple |
| R2: metrica interna de evaluacion y conclusion | Correlacion cofenetica y silueta; seccion 5.4 | Cumple |
| R3: KMP, Boyer-Moore, Rabin-Karp sin funciones nativas | `src/patrones.py` | Cumple |
| R3: ocurrencias con documento, posicion y fragmento resaltado | `/ui/patterns` | Cumple |
| R3: tablas auxiliares, hash rodante, colisiones, graficas de iteraciones | Seccion 6.2 y `docs/figuras/patron_*.png` | Cumple |
| R3: Big O frente a tiempos reales | Seccion 6.3, tablas y graficas | Cumple |
| R4: despliegue con enlace publico | `Procfile`, `render.yaml`, README | **Pendiente del grupo** (publicar y reemplazar `ENLACE_PUBLICO_DE_RENDER`) |
| R4: documento de diseno con arquitectura y detalles por requerimiento | `docs/DOCUMENTO_TECNICO_FINAL.*` | Cumple |
| Declaracion de uso de IA | Seccion 10 (borrador) | **El grupo debe revisarla** |
| Pruebas unitarias y manejo de errores | `tests/` (`python -m pytest -q`) | Cumple |
| Corre desde cero siguiendo el README | Probado en un entorno limpio (ver README) | Cumple |


## 3. Pendientes del grupo antes de entregar

1. Subir el repositorio a GitHub, crear el servicio en Render y copiar la URL en el documento (reemplazar `ENLACE_PUBLICO_DE_RENDER`).
2. Leer y ajustar la seccion 10 (declaracion de IA) a lo que hizo cada integrante.
3. Verificar las referencias bibliograficas (se citaron de memoria).
4. Repetir `python scripts/generar_evidencias.py` y `python scripts/generar_documentos.py` en su equipo si quieren tiempos de su maquina.
5. Practicar con la guia de sustentacion.

## 4. Limitaciones conocidas

- El script opcional de embeddings tipo Transformer (`generar_embeddings.py sbert`) no se ejecuto.
- Las pruebas contra scipy son opcionales (se omiten si scipy no esta instalado).
- La carpeta `pdfs/` no viaja en el repositorio; `scripts/extraer_corpus.py` solo hace falta si se quiere regenerar el corpus.

