"""Documentos de apoyo: DOCUMENTACION_TECNICA, GUIA_SUSTENTACION_PROYECTO y HOJA_DE_RUTA_COMPLETA."""
from _md import f, tabla


def documentacion_tecnica(ev):
    cc = ev["clustering"]["criterios"]
    pt = ev["patron"]
    L = []
    w = L.append
    w("# Documentacion tecnica del proyecto\n")
    w("Formato por componente: **que hace**, **donde esta**, **funciones clave**, **que decir en la sustentacion** y **ejemplo manual**. "
      "Los numeros provienen de `docs/evidencias/evidencias.json` (generado por `scripts/generar_evidencias.py`).\n")
    w("## 0. Mapa del repositorio\n")
    w("```text\napi.py  Procfile  render.yaml  requirements.txt  requirements-dev.txt\nsrc/        estructuras_datos, preprocesamiento, similitud_clasica, similitud_embeddings, comparacion,\n            clustering, patrones, benchmark_patrones, visualizacion, corpus, docs_algoritmos, paths, api\nscripts/    extraer_corpus, generar_embeddings, generar_evidencias, generar_documentos (+ _md, doc_final, doc_apoyo)\ndata/processed/  corpus.json, corpus_limpio.json, reporte_calidad.json, embeddings_glove.json, embeddings_fasttext.json\nstatic/     styles.css, app.js, modules/<modulo>/index.html\nmodules/    README por modulo (proposito, archivos, entradas, salidas, evidencia)\ntests/      pytest (estructuras, preprocesamiento, similitud, clustering, patrones, corpus/API, extraccion)\ndocs/       DOCUMENTO_TECNICO_FINAL (.md/.docx/.pdf), esta documentacion, guia, hoja de ruta, figuras, evidencias\n```\n")
    w("## 1. Estructuras de datos propias\n")
    w("- **Que hace:** reemplaza funciones de alto nivel por estructuras escritas con listas y bucles.\n- **Donde:** `src/estructuras_datos.py`.\n"
      "- **Clave:** `ListaDinamica`, `Pila`, `TablaHashSimple` (direccionamiento abierto con redimension), `ConjuntoHash`, `crear_matriz`, `ordenar_por_mezcla` (merge sort estable O(n log n)), `potencia_modular` (exponenciacion binaria), `mediana`, `promedio`.\n"
      "- **Decir:** \"La tabla hash usa sondeo lineal y se redimensiona al 70 % de carga; el ordenamiento es merge sort estable porque necesito conservar el orden de los empates.\"\n"
      "- **Ejemplo manual:** `potencia_modular(256, 11, 101)` eleva al cuadrado reduciendo modulo 101 en cada paso (O(log 11) multiplicaciones).\n")
    w("## 2. Corpus y preprocesamiento\n")
    w("- **Que hace:** convierte 20 PDFs en `corpus.json` y limpia el texto.\n- **Donde:** `scripts/extraer_corpus.py` (offline), `src/preprocesamiento.py`, `src/corpus.py`.\n"
      "- **Clave:** `localizar_abstract`, `unir_guiones`, `evaluar_calidad`, `a_minusculas`, `limpiar_signos`, `tokenizar`, `quitar_stopwords`, `stem_simple`, `preprocesar`.\n"
      "- **Decir:** \"La extraccion es un script offline; la app solo lee JSON. Los guiones de fin de linea se unen solo si la palabra resultante existe en el vocabulario. El #14 trae una cita bibliografica pegada en el PDF original: guardamos el original y la correccion.\"\n"
      "- **Ejemplo manual:** `AI-driven assessments (2023)` -> minusculas -> sin signos `ai driven assessments` -> stemming `ai driven assessment`.\n")
    w("## 3. Requerimiento 1: similitud\n")
    w("- **Donde:** `src/similitud_clasica.py`, `src/similitud_embeddings.py`, `src/comparacion.py`; pagina `/ui/similarity`.\n"
      "- **Clave:** `levenshtein_matriz`/`levenshtein_distancia`, `needleman_wunsch_matriz`/`_alineamiento`/`_normalizado`, `construir_vocabulario`, `calcular_idf`, `vector_tfidf`, `coseno_vectores`, `jaccard`, `coseno`, `distancia_euclidiana`, `comparar`, `detalle_par`.\n"
      "- **Decir:** \"Levenshtein y Needleman-Wunsch usan la misma tabla de programacion dinamica con distinta recurrencia. TF-IDF se calcula con IDF suavizado sobre los 20 abstracts. Los embeddings se calcularon offline; la web solo lee los vectores y calcula el coseno a mano.\"\n"
      "- **Resultados del caso (#%d y #%d):** %s.\n" % (ev["caso"]["a"], ev["caso"]["b"], ", ".join("%s = %s" % (k, f(v, 3)) for k, v in ev["caso_scores"].items())))
    w("- **Ejemplo manual (Levenshtein):** `kitten -> sitting`: sustituir k por s, e por i y anadir g = **3** operaciones.\n"
      "- **Ejemplo manual (Jaccard):** A = {a, b, c}, B = {b, c, d}: interseccion 2, union 4, J = 0,5.\n")
    w("## 4. Requerimiento 2: clustering\n")
    w("- **Donde:** `src/clustering.py`, `src/visualizacion.py` (dendrogramas); pagina `/ui/clustering`.\n"
      "- **Clave:** `matriz_distancias`, `agrupar` (historial de fusiones), `distancias_cofeneticas`, `correlacion_cofenetica`, `cortar_en_k`, `silueta`, `comparar_criterios`, `coordenadas_dendrograma`.\n"
      "- **Decir:** \"Cada fusion se guarda como (a, b, distancia, tamano); el dendrograma se dibuja desde ese historial. Elegimos el criterio con mayor correlacion cofenetica: %s (%s). Verificamos contra scipy solo en pruebas: coinciden.\"\n" % (
          cc[ev["clustering"]["mejor"]]["nombre"], f(cc[ev["clustering"]["mejor"]]["ccc"])))
    w("- **Ejemplo manual:** puntos 0, 1, 5, 7. Single: une (0,1) a 1, (5,7) a 2 y los grupos a min(5,7,4,6) = **4**. Complete: ultima altura max(...) = **7**. Average: (5+7+4+6)/4 = **5,5**.\n")
    w("## 5. Requerimiento 3: patrones\n")
    w("- **Donde:** `src/patrones.py`, `src/benchmark_patrones.py`; pagina `/ui/patterns`.\n"
      "- **Clave:** `kmp_tabla_lps`, `kmp_buscar`, `bm_tabla_caracter_malo`, `bm_tabla_sufijo_bueno`, `bm_buscar`, `rk_hash`, `rk_buscar`, `ejecutar`, `buscar_en_corpus`, `comparar_algoritmos`.\n"
      "- **Decir:** \"Los tres devuelven las mismas posiciones, incluso superpuestas (lo comprobamos con 2.500 casos aleatorios). Rabin-Karp verifica cada coincidencia de hash; con modulo pequeno aparecen colisiones, con el primo grande no.\"\n")
    w("- **Ejemplo manual (LPS):** `ABABCABAB` -> `[0,0,1,2,0,1,2,3,4]`. **Caso real:** `%s` -> `%s`.\n" % (pt["patron"], pt["lps"]))
    w("- **Ejemplo manual (Rabin-Karp):** B = 10, q = 13, texto `3141592`, patron `415` (m = 3). hash(415) = 415 mod 13 = 12; ventana `314` = 314 mod 13 = 2; B^(m-1) = 100 mod 13 = 9. "
      "Rodar: (2 - 3*9)*10 + 1 = -249 mod 13 = 11, que es el hash directo de `141` (141 mod 13 = 11). Si un hash coincide con el del patron, se verifica caracter por caracter.\n")
    w("## 6. Web, API y despliegue\n")
    w("- **Donde:** `src/api.py`, `static/`, `Procfile`, `render.yaml`, `src/paths.py`.\n- **Endpoints:** ver la pagina `/ui/docs`.\n"
      "- **Decir:** \"La app solo lee JSON y calcula; no carga modelos. `paths.py` usa variables de entorno y una carpeta temporal si no puede escribir (Render).\"\n")
    return "\n".join(L) + "\n"


def guia(ev):
    cc = ev["clustering"]["criterios"]
    mejor = ev["clustering"]["mejor"]
    pt = ev["patron"]
    sint = ev["benchmark"]["sinteticos"]
    L = []
    w = L.append
    w("# Guia de sustentacion\n")
    w("Objetivo: que cada integrante pueda explicar **cada linea** y responder al profesor. Lea primero la secuencia de demostracion y luego las preguntas.\n")
    w("## 1. Secuencia de demostracion (10 minutos)\n")
    w("1. **Corpus** (`/ui/corpus`): 20/20 abstracts validados; abrir el #14 y explicar la cita pegada en el PDF original; mostrar el preprocesamiento paso a paso.\n"
      "2. **Similitud** (`/ui/similarity`): elegir #%d y #%d, comparar, abrir *Ver calculo detallado* (producto punto, normas, angulo) y la matriz de calor.\n" % (ev["caso"]["a"], ev["caso"]["b"]) +
      "3. **Clustering** (`/ui/clustering`): tabla de metricas, dendrograma de cada criterio, cambiar k y ver los grupos.\n"
      "4. **Patrones** (`/ui/patterns`): buscar `%s`, ver las posiciones, *Iteraciones* de los tres algoritmos y *Medir tiempos*.\n" % pt["patron"] +
      "5. **Pruebas:** `python -m pytest -q` en vivo.\n")
    w("## 2. Que debe saber explicar cada uno\n")
    w(tabla(["Tema", "Una frase", "Donde mirar el codigo"], [
        ["Levenshtein", "Minimo de inserciones/borrados/sustituciones; tabla de programacion dinamica O(m*n)", "`levenshtein_matriz`"],
        ["Needleman-Wunsch", "Igual que Levenshtein pero maximiza puntaje (+1, -1, -1) y permite recuperar el alineamiento", "`needleman_wunsch_alineamiento`"],
        ["TF-IDF + coseno", "Peso = frecuencia en el documento x rareza en el corpus; coseno = angulo entre vectores", "`vector_tfidf`, `coseno_vectores`"],
        ["Jaccard", "Terminos compartidos / terminos totales", "`jaccard`"],
        ["Embeddings", "Vectores densos de palabras preentrenados; promedio por abstract; coseno y euclidiana a mano", "`similitud_embeddings.py`, `generar_embeddings.py`"],
        ["Clustering", "Fusionar siempre los dos clusters mas cercanos; el criterio define 'cercano' (min, max, promedio)", "`agrupar`"],
        ["Cofenetica y silueta", "Fidelidad del arbol a las distancias; cohesion frente a separacion de los grupos", "`correlacion_cofenetica`, `silueta`"],
        ["KMP", "Tabla LPS evita retroceder en el texto", "`kmp_tabla_lps`, `kmp_buscar`"],
        ["Boyer-Moore", "Compara de derecha a izquierda y salta con caracter malo y sufijo bueno", "`bm_buscar`"],
        ["Rabin-Karp", "Compara hashes rodantes y verifica; las colisiones son falsos positivos", "`rk_buscar`"],
    ]))
    w("\n## 3. Preguntas tipicas del profesor y respuestas cortas\n")
    qa = [
        ("Por que no uso scipy ni sklearn?", "El enunciado exige implementar los algoritmos explicitamente. scipy solo aparece en las pruebas para verificar que mis alturas de fusion y mi correlacion cofenetica coinciden."),
        ("Por que los embeddings no se calculan en la web?", "Los modelos pesan cientos de MB; no caben en el plan gratuito de Render. Se calculan una vez con `generar_embeddings.py` y la app lee `embeddings_*.json`."),
        ("Que modelos de embeddings usaron y como obtienen el vector del abstract?", "GloVe y fastText de 300 dimensiones. El vector es el promedio de los vectores de las palabras del abstract (sin stopwords), normalizado. No son modelos Transformer."),
        ("Por que los embeddings dan 0,9 para casi todo?", "Todos los abstracts comparten un vector dominante (el coseno de cada uno con la media del corpus es de al menos %s en GloVe y %s en fastText). Solo es util comparar el orden de los pares, no el valor absoluto." % (
            f(ev["verif"]["emb"]["glove"]["cos_min_a_la_media"], 2), f(ev["verif"]["emb"]["fasttext"]["cos_min_a_la_media"], 2))),
        ("Por que Levenshtein da valores parecidos para todos los pares?", "Mide la forma de la cadena; medimos que su orden depende de la razon de longitudes (Spearman %s). No mide tema." % f(ev["verif"]["spearman_lev_vs_razon_longitud"], 2)),
        ("Cual es la complejidad de Levenshtein y como se reduce el espacio?", "O(m*n) en tiempo; con dos filas el espacio baja de O(m*n) a O(min(m,n))."),
        ("Que es el IDF suavizado y por que?", "ln((1+N)/(1+df)) + 1. Evita que un termino presente en todos los documentos tenga peso 0 y evita dividir por cero."),
        ("Como normalizan Needleman-Wunsch a [0,1]?", "(puntaje - minimo)/(maximo - minimo), con maximo = min(m,n) - |m-n| y minimo = -(m+n), las cotas teoricas con +1/-1/-1."),
        ("Por que Average y no Ward?", "El enunciado pide tres criterios; Ward requiere distancias euclidianas y aqui la distancia natural es 1 - coseno."),
        ("Por que Average es el mejor?", "Mayor correlacion cofenetica: %s frente a %s (Single) y %s (Complete)." % (f(cc["average"]["ccc"], 3), f(cc["single"]["ccc"], 3), f(cc["complete"]["ccc"], 3))),
        ("La silueta es muy baja; eso invalida el resultado?", "No, indica que los abstracts forman una nube homogenea y sin grupos nitidos (maximo %s). Por eso la decision se apoya en la cofenetica y lo declaramos." % f(max(cc[k]["mejor_silueta"] for k in cc), 3)),
        ("Que es el encadenamiento de Single?", "Single une grupos por un solo par cercano; con k = 4 deja tres documentos aislados y un grupo grande. Se ve en el dendrograma como una escalera."),
        ("Cual es la complejidad de su clustering?", "O(n^3) tiempo y O(n^2) espacio; con n = 20 es instantaneo. Existen versiones O(n^2) con actualizacion de distancias, pero esta deja la definicion de cada criterio a la vista."),
        ("Como se dibuja el dendrograma sin scipy?", "`coordenadas_dendrograma` convierte el historial en segmentos (x1,y1,x2,y2): dos verticales hasta la altura de fusion y una horizontal que las une."),
        ("Que tabla usa KMP y por que no retrocede?", "La tabla LPS (prefijo que tambien es sufijo). Ante una falla, el patron salta a lps[j-1] y el indice del texto nunca baja; por eso O(n)."),
        ("Cual es la complejidad de Boyer-Moore?", "Preprocesamiento O(m + s); busqueda mejor O(n/m), promedio ~O(n), peor O(n*m). Lo medimos: con todas las posiciones coincidiendo hizo %d comparaciones frente a %d de KMP." % (
            sint[2]["algoritmos"]["boyer-moore"]["comparaciones"], sint[2]["algoritmos"]["kmp"]["comparaciones"])),
        ("Por que usan caracter malo Y sufijo bueno?", "El enunciado permite uno o ambos; el avance es el maximo de los dos, y el sufijo bueno compensa los casos donde el caracter malo daria avances pequenos."),
        ("Que es una colision en Rabin-Karp?", "Dos cadenas distintas con el mismo hash. Por eso cada coincidencia de hash se verifica caracter por caracter. Con modulo 101 hubo %d colisiones; con el primo grande, 0." % [x for x in pt["colisiones_por_modulo"] if x["modulo"] == 101][0]["colisiones"]),
        ("Como funciona el hash rodante?", "h(s+1) = ((h(s) - T[s]*B^(m-1))*B + T[s+m]) mod q: quita el caracter que sale y agrega el que entra en O(1)."),
        ("Por que Rabin-Karp es el mas lento si hace menos comparaciones?", "Porque en cada ventana hace multiplicaciones y modulo; el conteo de comparaciones de caracteres no es el unico costo."),
        ("Como saben que los tres algoritmos coinciden?", "`comparar_algoritmos` los corre sobre el corpus y verifica igualdad de posiciones; ademas hay 2.500 casos aleatorios contra una referencia independiente en `tests/test_patrones.py`."),
        ("Que hacen con mayusculas y posiciones?", "Por defecto no distingue mayusculas: convierte texto y patron con `a_minusculas`, que conserva la longitud, asi las posiciones valen para el texto original."),
        ("Que pasa con entradas invalidas?", "Patron vacio o de mas de 200 caracteres, texto no cadena o algoritmo desconocido -> `ErrorPatron` (HTTP 400). Patron mas largo que el texto -> 0 ocurrencias. Articulo inexistente -> 404."),
        ("Por que Needleman-Wunsch y Levenshtein tardan?", "Recorren matrices de cientos x cientos de celdas por par (unos %s ms por par en nuestras mediciones); por eso la web limita la comparacion a 6 articulos." % f(ev["tiempos_ms_por_par"]["levenshtein"]["promedio"], 0)),
        ("Que uso hicieron de IA generativa?", "Esta declarado en la seccion 10 del documento tecnico: apoyo en codigo, pruebas y redaccion; nosotros revisamos, ejecutamos y sustentamos. Ajusten esa seccion a lo que realmente hizo cada uno."),
        ("Que limitaciones tiene el trabajo?", "20 abstracts en ingles; stemming simple; embeddings promediados (no Transformer); silueta baja; tiempos medidos en una sola maquina."),
    ]
    for i, (p_, r_) in enumerate(qa, 1):
        w("**%d. %s**  \n%s\n" % (i, p_, r_))
    w("## 4. Ejercicios manuales para practicar\n")
    w("1. Llenar a mano la matriz de Levenshtein de `gato` y `pato` (resultado 1).\n"
      "2. Calcular la tabla LPS de `ABAB` (`[0,0,1,2]`) y de `AABAA` (`[0,1,0,1,2]`).\n"
      "3. Con puntos 0, 1, 5, 7, hacer Single, Complete y Average (alturas en `tests/test_clustering.py`).\n"
      "4. Con TF-IDF, dados df y conteos, calcular IDF suavizado de un termino con N = 20.\n")
    w("## 5. Cosas que NO decir\n")
    w("- \"Los embeddings entienden el significado\": son promedios de vectores de palabras y comprimen las diferencias.\n"
      "- \"Average es el mejor\" sin mencionar que la silueta es baja.\n"
      "- Cifras de tiempo como absolutas: dependen de la maquina; lo que importa es la forma de crecimiento y el conteo de comparaciones.\n")
    return "\n".join(L) + "\n"


def hoja_de_ruta(ev):
    L = []
    w = L.append
    w("# Hoja de ruta y lista de verificacion\n")
    w("## 1. Estado por fase\n")
    w(tabla(["Fase", "Contenido", "Estado"], [
        ["0", "Lectura del proyecto anterior, plan y estructura", "Completa"],
        ["1", "Extraccion de 20 abstracts, reporte de calidad y preprocesamiento", "Completa (20/20 validados)"],
        ["2", "Requerimiento 1: codigo, pruebas, pagina web y documentacion", "Completa"],
        ["3", "Requerimiento 2", "Completa"],
        ["4", "Requerimiento 3", "Completa"],
        ["5", "Integracion, interfaz final y archivos de despliegue", "Completa; **el despliegue en Render lo realiza el grupo** (README)"],
        ["6", "Documento tecnico, guia de sustentacion y revision", "Completa (borradores: el grupo debe revisarlos)"],
    ]))
    w("\n## 2. Verificacion contra el enunciado\n")
    w(tabla(["Requisito del enunciado", "Evidencia", "Estado"], [
        ["20 PDFs: titulo, autores y abstract; foco en el abstract", "`data/processed/corpus.json`, `reporte_calidad.json`", "Cumple"],
        ["R1: seleccion dinamica de 2 o mas articulos", "`/ui/similarity` (2 a 6)", "Cumple"],
        ["R1: 4 algoritmos clasicos desde cero", "`src/similitud_clasica.py`", "Cumple"],
        ["R1: 2 modelos de IA con embeddings, similitud coseno/euclidiana", "GloVe y fastText; `src/similitud_embeddings.py`", "Cumple (modelos de palabras promediados)"],
        ["R1: caso de estudio, paso a paso y analisis critico", "Documento tecnico, seccion 4", "Cumple"],
        ["R2: 3 criterios de enlace desde cero, historial, dendrogramas propios", "`src/clustering.py`, `docs/figuras/dendrograma_*.png`", "Cumple"],
        ["R2: metrica interna de evaluacion y conclusion", "Correlacion cofenetica y silueta; seccion 5.4", "Cumple"],
        ["R3: KMP, Boyer-Moore, Rabin-Karp sin funciones nativas", "`src/patrones.py`", "Cumple"],
        ["R3: ocurrencias con documento, posicion y fragmento resaltado", "`/ui/patterns`", "Cumple"],
        ["R3: tablas auxiliares, hash rodante, colisiones, graficas de iteraciones", "Seccion 6.2 y `docs/figuras/patron_*.png`", "Cumple"],
        ["R3: Big O frente a tiempos reales", "Seccion 6.3, tablas y graficas", "Cumple"],
        ["R4: despliegue con enlace publico", "`Procfile`, `render.yaml`, README", "**Pendiente del grupo** (publicar y reemplazar `ENLACE_PUBLICO_DE_RENDER`)"],
        ["R4: documento de diseno con arquitectura y detalles por requerimiento", "`docs/DOCUMENTO_TECNICO_FINAL.*`", "Cumple"],
        ["Declaracion de uso de IA", "Seccion 10 (borrador)", "**El grupo debe revisarla**"],
        ["Pruebas unitarias y manejo de errores", "`tests/` (`python -m pytest -q`)", "Cumple"],
        ["Corre desde cero siguiendo el README", "Probado en un entorno limpio (ver README)", "Cumple"],
    ]))
    w("\n## 3. Pendientes del grupo antes de entregar\n")
    w("1. Subir el repositorio a GitHub, crear el servicio en Render y copiar la URL en el documento (reemplazar `ENLACE_PUBLICO_DE_RENDER`).\n"
      "2. Leer y ajustar la seccion 10 (declaracion de IA) a lo que hizo cada integrante.\n"
      "3. Verificar las referencias bibliograficas (se citaron de memoria).\n"
      "4. Repetir `python scripts/generar_evidencias.py` y `python scripts/generar_documentos.py` en su equipo si quieren tiempos de su maquina.\n"
      "5. Practicar con la guia de sustentacion.\n")
    w("## 4. Limitaciones conocidas\n")
    w("- El script opcional de embeddings tipo Transformer (`generar_embeddings.py sbert`) no se ejecuto.\n"
      "- Las pruebas contra scipy son opcionales (se omiten si scipy no esta instalado).\n"
      "- La carpeta `pdfs/` no viaja en el repositorio; `scripts/extraer_corpus.py` solo hace falta si se quiere regenerar el corpus.\n")
    return "\n".join(L) + "\n"
