# Requerimiento 2: clustering jerarquico

- **Proposito:** Agrupar los 20 abstracts con Single, Complete y Average Linkage y evaluar con metricas internas.
- **Archivos:** src/clustering.py, src/visualizacion.py, static/modules/clustering/index.html
- **Entradas:** Vectores TF-IDF de los 20 abstracts
- **Salidas:** Historial de fusiones, dendrogramas PNG, correlacion cofenetica, silueta, grupos por k
- **Evidencia para sustentar:** Seccion 5 del documento tecnico; tests/test_clustering.py (incluye verificacion contra scipy)
