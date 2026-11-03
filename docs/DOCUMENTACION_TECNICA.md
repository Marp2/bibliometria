# Documentacion tecnica del proyecto

Formato por componente: **que hace**, **donde esta**, **funciones clave**, **que decir en la sustentacion** y **ejemplo manual**. Los numeros provienen de `docs/evidencias/evidencias.json` (generado por `scripts/generar_evidencias.py`).

## 0. Mapa del repositorio

```text
api.py  Procfile  render.yaml  requirements.txt  requirements-dev.txt
src/        estructuras_datos, preprocesamiento, similitud_clasica, similitud_embeddings, comparacion,
            clustering, patrones, benchmark_patrones, visualizacion, corpus, docs_algoritmos, paths, api
scripts/    extraer_corpus, generar_embeddings, generar_evidencias, generar_documentos (+ _md, doc_final, doc_apoyo)
data/processed/  corpus.json, corpus_limpio.json, reporte_calidad.json, embeddings_glove.json, embeddings_fasttext.json
static/     styles.css, app.js, modules/<modulo>/index.html
modules/    README por modulo (proposito, archivos, entradas, salidas, evidencia)
tests/      pytest (estructuras, preprocesamiento, similitud, clustering, patrones, corpus/API, extraccion)
docs/       DOCUMENTO_TECNICO_FINAL (.md/.docx/.pdf), esta documentacion, guia, hoja de ruta, figuras, evidencias
```

## 1. Estructuras de datos propias

- **Que hace:** reemplaza funciones de alto nivel por estructuras escritas con listas y bucles.
- **Donde:** `src/estructuras_datos.py`.
- **Clave:** `ListaDinamica`, `Pila`, `TablaHashSimple` (direccionamiento abierto con redimension), `ConjuntoHash`, `crear_matriz`, `ordenar_por_mezcla` (merge sort estable O(n log n)), `potencia_modular` (exponenciacion binaria), `mediana`, `promedio`.
- **Decir:** "La tabla hash usa sondeo lineal y se redimensiona al 70 % de carga; el ordenamiento es merge sort estable porque necesito conservar el orden de los empates."
- **Ejemplo manual:** `potencia_modular(256, 11, 101)` eleva al cuadrado reduciendo modulo 101 en cada paso (O(log 11) multiplicaciones).

## 2. Corpus y preprocesamiento

- **Que hace:** convierte 20 PDFs en `corpus.json` y limpia el texto.
- **Donde:** `scripts/extraer_corpus.py` (offline), `src/preprocesamiento.py`, `src/corpus.py`.
- **Clave:** `localizar_abstract`, `unir_guiones`, `evaluar_calidad`, `a_minusculas`, `limpiar_signos`, `tokenizar`, `quitar_stopwords`, `stem_simple`, `preprocesar`.
- **Decir:** "La extraccion es un script offline; la app solo lee JSON. Los guiones de fin de linea se unen solo si la palabra resultante existe en el vocabulario. El #14 trae una cita bibliografica pegada en el PDF original: guardamos el original y la correccion."
- **Ejemplo manual:** `AI-driven assessments (2023)` -> minusculas -> sin signos `ai driven assessments` -> stemming `ai driven assessment`.

## 3. Requerimiento 1: similitud

- **Donde:** `src/similitud_clasica.py`, `src/similitud_embeddings.py`, `src/comparacion.py`; pagina `/ui/similarity`.
- **Clave:** `levenshtein_matriz`/`levenshtein_distancia`, `needleman_wunsch_matriz`/`_alineamiento`/`_normalizado`, `construir_vocabulario`, `calcular_idf`, `vector_tfidf`, `coseno_vectores`, `jaccard`, `coseno`, `distancia_euclidiana`, `comparar`, `detalle_par`.
- **Decir:** "Levenshtein y Needleman-Wunsch usan la misma tabla de programacion dinamica con distinta recurrencia. TF-IDF se calcula con IDF suavizado sobre los 20 abstracts. Los embeddings se calcularon offline; la web solo lee los vectores y calcula el coseno a mano."
- **Resultados del caso (#2 y #6):** levenshtein = 0.327, needleman-wunsch = 0.658, tfidf-coseno = 0.329, jaccard = 0.173, emb-glove = 0.951, emb-fasttext = 0.974.

- **Ejemplo manual (Levenshtein):** `kitten -> sitting`: sustituir k por s, e por i y anadir g = **3** operaciones.
- **Ejemplo manual (Jaccard):** A = {a, b, c}, B = {b, c, d}: interseccion 2, union 4, J = 0,5.

## 4. Requerimiento 2: clustering

- **Donde:** `src/clustering.py`, `src/visualizacion.py` (dendrogramas); pagina `/ui/clustering`.
- **Clave:** `matriz_distancias`, `agrupar` (historial de fusiones), `distancias_cofeneticas`, `correlacion_cofenetica`, `cortar_en_k`, `silueta`, `comparar_criterios`, `coordenadas_dendrograma`.
- **Decir:** "Cada fusion se guarda como (a, b, distancia, tamano); el dendrograma se dibuja desde ese historial. Elegimos el criterio con mayor correlacion cofenetica: Average Linkage (UPGMA) (0.8030). Verificamos contra scipy solo en pruebas: coinciden."

- **Ejemplo manual:** puntos 0, 1, 5, 7. Single: une (0,1) a 1, (5,7) a 2 y los grupos a min(5,7,4,6) = **4**. Complete: ultima altura max(...) = **7**. Average: (5+7+4+6)/4 = **5,5**.

## 5. Requerimiento 3: patrones

- **Donde:** `src/patrones.py`, `src/benchmark_patrones.py`; pagina `/ui/patterns`.
- **Clave:** `kmp_tabla_lps`, `kmp_buscar`, `bm_tabla_caracter_malo`, `bm_tabla_sufijo_bueno`, `bm_buscar`, `rk_hash`, `rk_buscar`, `ejecutar`, `buscar_en_corpus`, `comparar_algoritmos`.
- **Decir:** "Los tres devuelven las mismas posiciones, incluso superpuestas (lo comprobamos con 2.500 casos aleatorios). Rabin-Karp verifica cada coincidencia de hash; con modulo pequeno aparecen colisiones, con el primo grande no."

- **Ejemplo manual (LPS):** `ABABCABAB` -> `[0,0,1,2,0,1,2,3,4]`. **Caso real:** `perspectives` -> `[0, 0, 0, 0, 1, 2, 0, 0, 0, 0, 0, 0]`.

- **Ejemplo manual (Rabin-Karp):** B = 10, q = 13, texto `3141592`, patron `415` (m = 3). hash(415) = 415 mod 13 = 12; ventana `314` = 314 mod 13 = 2; B^(m-1) = 100 mod 13 = 9. Rodar: (2 - 3*9)*10 + 1 = -249 mod 13 = 11, que es el hash directo de `141` (141 mod 13 = 11). Si un hash coincide con el del patron, se verifica caracter por caracter.

## 6. Web, API y despliegue

- **Donde:** `src/api.py`, `static/`, `Procfile`, `render.yaml`, `src/paths.py`.
- **Endpoints:** ver la pagina `/ui/docs`.
- **Decir:** "La app solo lee JSON y calcula; no carga modelos. `paths.py` usa variables de entorno y una carpeta temporal si no puede escribir (Render)."

