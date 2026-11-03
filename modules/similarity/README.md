# Requerimiento 1: similitud textual

- **Proposito:** Comparar 2 a 6 abstracts con 4 algoritmos clasicos y 2 modelos de embeddings.
- **Archivos:** src/similitud_clasica.py, src/similitud_embeddings.py, src/comparacion.py, static/modules/similarity/index.html
- **Entradas:** Lista de ids de articulos (POST /api/similarity)
- **Salidas:** Similitud [0,1] por par y algoritmo, calculo detallado (/api/similarity/detalle), mapa de calor
- **Evidencia para sustentar:** Seccion 4 del documento tecnico; tests/test_similitud.py
