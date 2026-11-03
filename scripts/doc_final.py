"""Construye docs/DOCUMENTO_TECNICO_FINAL.md con los numeros reales de docs/evidencias/evidencias.json."""
import os

from _md import etiqueta, f, historial_md, matriz_dp, tabla

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _kb_datos():
    carpeta = os.path.join(_RAIZ, "data", "processed")
    total = 0
    for n in os.listdir(carpeta):
        if n.endswith(".json"):
            total += os.path.getsize(os.path.join(carpeta, n))
    return "%d" % round(total / 1024.0)


NOMBRES = {"levenshtein": "Levenshtein", "needleman-wunsch": "Needleman-Wunsch", "tfidf-coseno": "Coseno TF-IDF",
           "jaccard": "Jaccard", "emb-glove": "GloVe (coseno)", "emb-fasttext": "fastText (coseno)"}
CL = ("levenshtein", "needleman-wunsch", "tfidf-coseno", "jaccard", "emb-glove", "emb-fasttext")


def construir(ev):
    c = ev["corpus"]
    caso, contr = ev["caso_scores"], ev["contraste_scores"]
    dpf, dpc = ev["dp_fragmento"], ev["dp_completo"]
    det = ev["detalle"]
    tf = det["tfidf"]
    jac = det["jaccard"]
    tc = ev["tokens_caso"]
    cla = ev["clustering"]
    pt = ev["patron"]
    bm = ev["benchmark"]
    maq = ev["maquina"]
    q = ev["calidad"]
    esc = bm["escalabilidad"]
    sint = bm["sinteticos"]
    mejor = cla["mejor"]
    cc = cla["criterios"]
    ver = ev["verificacion_scipy"]
    rk = pt["rk"]
    rkd = pt["rk_demo"]
    idx_a = {d["id"]: d for d in c["articulos"]}

    L = []
    w = L.append
    w("# Analisis de algoritmos en el contexto de la bibliometria\n")
    w("**Proyecto final - Analisis de Algoritmos - Universidad del Quindio, Programa de Ingenieria de Sistemas y Computacion, 2026-2**\n")
    w("**Integrantes:** Cristhian Camilo Lopez Grajales, Mariana Pineda Montenegro y Camila Hernandez Pena\n")
    w("**Dominio:** inteligencia artificial generativa y IA en educacion - **Corpus:** 20 articulos cientificos (solo se procesa el abstract)\n")
    w("**Aplicacion desplegada:** `ENLACE_PUBLICO_DE_RENDER` *(reemplazar por la URL real al desplegar; ver README)*\n")
    w("> Todos los numeros, tablas y figuras de este documento se generaron ejecutando el codigo del repositorio "
      "(`scripts/generar_evidencias.py`). Ningun resultado se escribio a mano. Tiempos medidos en: Python %s, %s, %s CPU(s)." % (
          maq["python"], maq["sistema"], maq["cpus"]))
    w("\n---\n")

    # ------------------------------------------------------------------ 1
    w("## 1. Introduccion\n")
    w("El analisis computacional de textos cientificos permite describir y comparar publicaciones con metodos cuantitativos. "
      "Este proyecto enfrenta el reto de procesar lenguaje natural no estructurado pasando de algoritmos y estructuras de datos clasicos "
      "a representaciones modernas basadas en IA. Sobre un corpus controlado de 20 articulos en PDF se implementaron, **desde cero**, "
      "tres familias de algoritmos: (1) similitud textual (cuatro clasicos y dos con embeddings), (2) clustering jerarquico con tres criterios de enlace "
      "y (3) busqueda exacta de patrones (KMP, Boyer-Moore y Rabin-Karp). Para cada una se presenta un caso de estudio con calculo paso a paso, "
      "un analisis critico y una contrastacion entre la complejidad teorica y los tiempos reales medidos. La aplicacion web esta construida con Flask y se despliega en Render.\n")
    w("**Restricciones respetadas.** Los algoritmos usan solo listas, bucles y estructuras propias (`src/estructuras_datos.py`). No se usan "
      "scipy, sklearn, numpy, pandas, difflib, `find()`, `index()`, `in` ni expresiones regulares en la logica de los algoritmos. "
      "Las librerias externas solo apoyan: `pypdf` (leer PDFs, script offline), modelos preentrenados (embeddings, script offline), `matplotlib` (graficas) y `Flask`/`gunicorn` (web).\n")

    # ------------------------------------------------------------------ 2
    w("## 2. Arquitectura y diseno\n")
    w("### 2.1 Diagrama de componentes\n")
    w("![Diagrama de componentes](figuras/arquitectura.png)\n")
    w("### 2.2 Flujo de datos\n")
    w("![Flujo de datos](figuras/flujo_datos.png)\n")
    w("**Idea central:** todo lo costoso o dependiente de librerias pesadas ocurre **fuera del servidor** (extraccion de PDFs y embeddings) y deja "
      "archivos JSON en `data/processed/`. El servidor solo lee esos JSON, ejecuta los algoritmos propios y dibuja. Asi la app cabe en el plan gratuito de Render.\n")
    w(tabla(["Capa", "Archivos", "Responsabilidad"], [
        ["Datos offline", "`scripts/extraer_corpus.py`, `scripts/generar_embeddings.py`", "PDF -> `corpus.json`, `reporte_calidad.json`, `embeddings_<modelo>.json`"],
        ["Estructuras propias", "`src/estructuras_datos.py`", "Lista dinamica, pila, tabla hash, conjuntos, matrices, ordenamiento por mezcla, minimo/maximo"],
        ["Preprocesamiento", "`src/preprocesamiento.py`", "Minusculas, tildes, signos, tokenizacion, stopwords (EN/ES), stemming simple"],
        ["Req. 1", "`src/similitud_clasica.py`, `src/similitud_embeddings.py`, `src/comparacion.py`", "Levenshtein, Needleman-Wunsch, TF-IDF+coseno, Jaccard, coseno/euclidiana sobre embeddings"],
        ["Req. 2", "`src/clustering.py`", "Single/Complete/Average, historial de fusiones, correlacion cofenetica, silueta"],
        ["Req. 3", "`src/patrones.py`, `src/benchmark_patrones.py`", "KMP, Boyer-Moore, Rabin-Karp y mediciones de tiempo"],
        ["Presentacion", "`src/visualizacion.py`, `src/api.py`, `static/`", "Graficas PNG, endpoints, 5 paginas web"],
        ["Configuracion", "`src/paths.py`, `Procfile`, `render.yaml`", "Rutas por variables de entorno (con carpeta temporal de respaldo) y despliegue"],
    ]))
    w("\n### 2.3 Decisiones de diseno\n")
    w(tabla(["Decision", "Alternativa descartada", "Motivo"], [
        ["Embeddings calculados una sola vez, fuera del servidor", "Cargar el modelo en la app", "Los modelos pesan cientos de MB o GB; no caben en el plan gratuito de Render"],
        ["Dos modelos de embeddings distintos: GloVe y fastText (300 d)", "Un solo modelo", "El enunciado exige dos; son algoritmos de entrenamiento distintos (co-ocurrencia global vs skip-gram con subpalabras)"],
        ["Levenshtein y Needleman-Wunsch sobre caracteres del texto limpio", "Nivel de palabra", "Cumple la forma clasica de programacion dinamica; ~0,18 s por par es viable en la web"],
        ["IDF suavizado ln((1+N)/(1+df))+1 con N = 20 abstracts", "IDF = ln(N/df)", "Evita IDF = 0 para terminos presentes en todos los documentos"],
        ["Distancia de clustering = 1 - coseno TF-IDF", "Distancia euclidiana", "El coseno ignora la longitud de cada abstract"],
        ["Criterios: Single, Complete y Average (UPGMA)", "Ward", "El enunciado pide tres y Ward requiere distancias euclidianas"],
        ["Metrica interna principal: correlacion cofenetica; apoyo: silueta", "Solo silueta", "La silueta es baja y casi plana en este corpus; la cofenetica mide fidelidad del arbol"],
        ["Clustering O(n^3) directo desde la matriz original", "Actualizacion de Lance-Williams", "Con n = 20 es instantaneo y la definicion de cada criterio queda visible en el codigo"],
        ["Busqueda de patrones sobre el abstract original, sin distinguir mayusculas por defecto", "Buscar en texto preprocesado", "Las posiciones y el resaltado deben corresponder al texto real; la conversion a minusculas conserva la longitud"],
        ["Rabin-Karp con base 256 y modulo primo 1.000.000.007", "Modulo pequeno", "Colisiones casi nulas; el modulo pequeno se usa solo para demostrar colisiones"],
        ["Un solo worker de gunicorn y cache en memoria", "Varios workers", "Plan gratuito de Render con poca memoria; los calculos son deterministas"],
    ]))

    # ------------------------------------------------------------------ 3
    w("\n## 3. Corpus y preprocesamiento\n")
    w("### 3.1 Extraccion\n")
    w("`scripts/extraer_corpus.py` lee las dos primeras paginas de cada PDF con `pypdf`, normaliza ligaduras tipograficas (por ejemplo \"fi\"), "
      "localiza el abstract entre su encabezado (`ABSTRACT`, `Abstract`, `A B S T R A C T`) y la siguiente marca (`Keywords`, `1. Introduction`...), "
      "une las palabras cortadas por guion de fin de linea **solo si la palabra unida existe en el vocabulario del corpus**, y guarda `corpus.json`. "
      "Los titulos y autores se verificaron manualmente contra la pagina 1 (los metadatos internos de los PDF son incompletos) y el script comprueba que cada titulo aparezca textual en la pagina.\n")
    w("Casos especiales documentados: el articulo #7 (dos columnas) usa un ancla de inicio manual, el #9 no tiene marca de fin y usa un ancla de fin manual, "
      "y el #14 trae en el PDF original una referencia bibliografica pegada dentro del abstract; se conserva el texto original en `abstract_original` y se elimina la cita en `abstract` (`correccion_manual`). "
      "Ademas se corrigieron dos artefactos de extraccion, tambien registrados en `correccion_manual`: en el #6 el PDF pierde el espacio antes de una ligadura (`researchfield` -> `research field`) y en el #17 un guion de salto de linea no resuelto (`holisti-cally` -> `holistically`).\n")
    w("### 3.2 Reporte de calidad\n")
    w("Resultado: **%d de %d abstracts validados** (sin residuos de citas ni palabras clave, longitud entre %d y %d palabras, inicio en mayuscula y cierre con punto, "
      "titulo verificado y concordancia >= 0,9 con una extraccion Java independiente).\n" % (
          q["ok"], q["total_extraidos"], min(r["palabras"] for r in q["detalle"]), max(r["palabras"] for r in q["detalle"])))
    w(tabla(["ID", "Autores", "Palabras", "Caracteres", "Titulo"],
            [[a["id"], len(a["autores"]), a["palabras"], a["caracteres"], a["titulo"]] for a in c["articulos"]], numericas=(0, 1, 2, 3)))
    w("\n### 3.3 Preprocesamiento escrito a mano\n")
    w(tabla(["Paso", "Que hace", "Por que"], [
        ["1. Minusculas", "A-Z y letras latinas acentuadas -> minuscula (conserva la longitud)", "`Education` y `education` son el mismo termino"],
        ["2. Sin tildes", "a, e, i, o, u, n con acento -> sin acento", "Unifica variantes en espanol"],
        ["3. Sin signos", "Todo lo que no sea letra a-z pasa a espacio (digitos, guiones, apostrofes)", "`AI-driven` -> `ai`, `driven`"],
        ["4. Tokenizacion", "Parte por espacios con un bucle", "Unidad minima de analisis"],
        ["5. Stopwords", "Descarta palabras vacias EN/ES y tokens de menos de 2 letras", "`ai` (2 letras) se conserva porque es el tema del corpus"],
        ["6. Stemming simple", "Reglas de sufijos (-ation, -ing, -ies, -ed, -es, -s...)", "Reduce variantes (learning/learner/learn)"],
    ]))
    w("\n**Ejemplo real (abstract #%d).** Primeros tokens finales: `%s ...`\n" % (ev["caso"]["a"], " ".join(ev["pre_ejemplo"]["tokens_finales"][:14])))
    w("**Efecto medido:** el corpus tiene %d tokens, %d tras quitar stopwords; el vocabulario baja de %d a %d terminos con stemming (%.1f %% menos). "
      "Por eso se usa stemming en TF-IDF, Jaccard y clustering, mientras que Levenshtein/Needleman-Wunsch usan el texto limpio sin stemming y los embeddings usan tokens sin stemming "
      "(los modelos preentrenados contienen palabras completas).\n" % (
          c["tokens_totales"], c["tokens_utiles"], c["vocab_sin_stemming"], c["vocab_con_stemming"],
          100.0 * (c["vocab_sin_stemming"] - c["vocab_con_stemming"]) / c["vocab_sin_stemming"]))
    w("El texto limpio de cada abstract se guarda en `data/processed/corpus_limpio.json`.\n")

    # ------------------------------------------------------------------ 4
    w("## 4. Requerimiento 1: similitud textual\n")
    w("### 4.1 Explicacion tecnica\n")
    w(tabla(["Algoritmo", "Tipo", "Entrada", "Salida [0,1]", "Tiempo", "Espacio"], [
        ["Levenshtein", "Clasico (prog. dinamica)", "Texto limpio, caracteres", "1 - D/max(m,n)", "O(m*n)", "O(min(m,n)); O(m*n) con matriz"],
        ["Needleman-Wunsch", "Clasico (prog. dinamica)", "Texto limpio, caracteres", "Puntaje normalizado con cotas teoricas", "O(m*n)", "O(n); O(m*n) con traceback"],
        ["Coseno TF-IDF", "Clasico (espacio vectorial)", "Tokens con stemming", "Coseno (>= 0 en TF-IDF)", "O(V) por par", "O(V) por documento"],
        ["Jaccard", "Clasico (conjuntos)", "Tokens con stemming", "|A inter B| / |A union B|", "O(m+n) promedio", "O(m+n)"],
        ["GloVe 300 d", "IA (embeddings)", "Vector promedio normalizado", "Coseno recortado a [0,1]", "O(d)", "O(d)"],
        ["fastText 300 d", "IA (embeddings)", "Vector promedio normalizado", "Coseno recortado a [0,1]", "O(d)", "O(d)"],
    ]))
    w("\n**Formulas.** Levenshtein: `D[i][j] = min(D[i-1][j]+1, D[i][j-1]+1, D[i-1][j-1]+costo)`. "
      "Needleman-Wunsch: `F[i][j] = max(F[i-1][j-1]+s, F[i-1][j]+gap, F[i][j-1]+gap)` con s = +1 (coincide), -1 (difiere) y gap = -1; "
      "normalizacion `(puntaje - minimo)/(maximo - minimo)` con `maximo = min(m,n) - |m-n|` y `minimo = -(m+n)`. "
      "TF = conteo/total de tokens; IDF = ln((1+N)/(1+df)) + 1; coseno = (u.v)/(|u||v|). Jaccard = |A inter B|/|A union B|. "
      "Euclidiana d = raiz(suma (ui - vi)^2), con similitud 1/(1+d).\n")
    w("**Embeddings (IA).** Se usaron dos modelos preentrenados de palabras, ambos de 300 dimensiones: `%s` (%s) y `%s` (%s). "
      "El vector de un abstract es el **promedio** de los vectores de sus palabras (tokens en minuscula, sin stopwords y sin stemming), normalizado a norma 1. "
      "Se calcula una sola vez con `scripts/generar_embeddings.py` y se guarda en `data/processed/embeddings_<modelo>.json`; la web solo lee los vectores. "
      "El coseno y la distancia euclidiana se calculan con nuestras funciones. Son modelos de vectores de palabras agregados, **no** modelos de lenguaje tipo Transformer.\n" % (
          ev["embeddings_caso"]["glove"]["modelo"], ev["embeddings_caso"]["glove"]["descripcion"],
          ev["embeddings_caso"]["fasttext"]["modelo"], ev["embeddings_caso"]["fasttext"]["descripcion"]))

    w("### 4.2 Caso de estudio\n")
    w("**Seleccion objetiva.** Se calcularon los 190 pares posibles entre los 20 abstracts. El par mas parecido segun el coseno TF-IDF es **#%d y #%d** (caso de estudio) y el menos parecido es #%d y #%d (contraste).\n" % (
        ev["caso"]["a"], ev["caso"]["b"], ev["caso"]["contraste"][0], ev["caso"]["contraste"][1]))
    w("**Abstract #%d** - *%s*\n\n> %s\n" % (ev["caso"]["a"], tc["titulo_a"], tc["abstract_a"]))
    w("**Abstract #%d** - *%s*\n\n> %s\n" % (ev["caso"]["b"], tc["titulo_b"], tc["abstract_b"]))

    w("#### 4.2.1 Levenshtein: llenado de la matriz\n")
    w("Matriz completa sobre los **primeros 10 caracteres** del texto limpio de cada abstract (`%s` y `%s`). La fila 0 y la columna 0 son el costo de insertar/borrar todo; "
      "cada celda toma el minimo de borrar (arriba + 1), insertar (izquierda + 1) o sustituir (diagonal + costo, 0 si los caracteres son iguales).\n" % (dpf["a"], dpf["b"]))
    w(matriz_dp(dpf["lev_matriz"], dpf["a"], dpf["b"]))
    w("\nDistancia del fragmento = **%d**. Sobre el texto limpio completo (%d y %d caracteres, matriz de %d x %d celdas) la distancia es **%d**, es decir similitud = 1 - %d/%d = **%s**.\n" % (
        dpf["lev_distancia"], dpc["longitud_a"], dpc["longitud_b"], dpc["longitud_a"] + 1, dpc["longitud_b"] + 1, dpc["levenshtein"],
        dpc["levenshtein"], max(dpc["longitud_a"], dpc["longitud_b"]), f(dpc["levenshtein_sim"])))

    w("#### 4.2.2 Needleman-Wunsch: matriz de puntajes y alineamiento\n")
    w("Mismos fragmentos, con coincidencia = +1, diferencia = -1 y hueco = -1. La fila 0 y la columna 0 valen `i * hueco`.\n")
    w(matriz_dp(dpf["nw_matriz"], dpf["a"], dpf["b"]))
    w("\nPuntaje del fragmento = **%d** (esquina inferior derecha). Alineamiento optimo recuperado con *traceback* (`-` = hueco):\n\n```text\n%s\n%s\n```\n" % (
        dpf["nw_puntaje"], dpf["nw_alineamiento_a"], dpf["nw_alineamiento_b"]))
    w("Sobre el texto completo: puntaje = **%d**, maximo teorico = %d, minimo teorico = %d, similitud normalizada = (%d - (%d)) / (%d - (%d)) = **%s**.\n" % (
        dpc["nw_puntaje"], dpc["nw_maximo"], dpc["nw_minimo"], dpc["nw_puntaje"], dpc["nw_minimo"], dpc["nw_maximo"], dpc["nw_minimo"], f(dpc["nw_sim"])))

    w("#### 4.2.3 Coseno con TF-IDF: vocabulario, TF, IDF, pesos, producto punto, normas y angulo\n")
    w("**Vocabulario.** Los %d abstracts forman un vocabulario de %d terminos (con stemming). Estos dos abstracts usan %d terminos distintos en total (union): "
      "|A| = %d terminos en #%d y |B| = %d en #%d.\n" % (20, tf["tamano_vocabulario"], tf["terminos_union"], jac["tamano_a"], ev["caso"]["a"], jac["tamano_b"], ev["caso"]["b"]))
    w("**IDF (calculado sobre los 20 abstracts, N = 20).** Ejemplos reales:\n")
    w(tabla(["Termino", "df", "IDF = ln(21/(1+df)) + 1"], [[e["termino"], e["df"], f(e["idf"])] for e in ev["idf_ejemplos"]], numericas=(1, 2)))
    w("\nUn termino raro (df bajo) pesa mas que uno que aparece en casi todos los abstracts.\n")
    w("**TF y pesos.** TF = conteo/total de tokens del abstract; peso = TF x IDF. Los 15 terminos con mayor aporte al producto punto (la tabla completa de %d terminos esta en el Anexo A):\n" % tf["terminos_union"])
    w(tabla(["Termino", "df", "IDF", "TF #%d" % ev["caso"]["a"], "TF #%d" % ev["caso"]["b"], "w #%d" % ev["caso"]["a"], "w #%d" % ev["caso"]["b"], "w x w"],
            [[t["termino"], t["df"], f(t["idf"], 3), f(t["tf_a"]), f(t["tf_b"]), f(t["w_a"]), f(t["w_b"]), f(t["producto"], 5)] for t in tf["terminos_mayor_aporte"][:15]],
            numericas=(1, 2, 3, 4, 5, 6, 7)))
    w("\n**Producto punto** = suma de w_A x w_B = **%s**.  **Normas:** |A| = raiz(suma w_A^2) = **%s**, |B| = **%s**.\n" % (
        f(tf["producto_punto"], 6), f(tf["norma_a"], 6), f(tf["norma_b"], 6)))
    w("**Coseno** = %s / (%s x %s) = **%s**.  **Angulo** = arccos(coseno) = **%s grados**.\n" % (
        f(tf["producto_punto"], 6), f(tf["norma_a"], 6), f(tf["norma_b"], 6), f(tf["coseno"], 6), f(tf["angulo_grados"], 2)))
    w("![Coseno TF-IDF entre los 20 abstracts](figuras/heatmap_tfidf_corpus.png)\n")

    w("#### 4.2.4 Jaccard: interseccion y union\n")
    w("|A| = %d, |B| = %d, **|A inter B| = %d**, **|A union B| = %d** -> J = %d/%d = **%s**.\n" % (
        jac["tamano_a"], jac["tamano_b"], len(jac["interseccion"]), jac["tamano_union"], len(jac["interseccion"]), jac["tamano_union"], f(jac["similitud"])))
    w("Terminos compartidos (con stemming): `%s`.\n" % "`, `".join(jac["interseccion"]))

    w("#### 4.2.5 Embeddings: como se obtiene el vector y su similitud\n")
    w("Pasos: (1) tokens del abstract sin stopwords y sin stemming; (2) se busca el vector de 300 dimensiones de cada palabra en el modelo; "
      "(3) se promedian los vectores encontrados; (4) se normaliza a norma 1; (5) se calcula coseno y distancia euclidiana entre los dos vectores.\n")
    filas = []
    for k in ("glove", "fasttext"):
        e = ev["embeddings_caso"][k]
        filas.append([e["modelo"], e["dimension"], "%d de %d (%s)" % (e["cobertura_a"]["con_vector"], e["cobertura_a"]["palabras"], f(e["cobertura_a"]["cobertura"], 3)),
                      "%d de %d (%s)" % (e["cobertura_b"]["con_vector"], e["cobertura_b"]["palabras"], f(e["cobertura_b"]["cobertura"], 3)),
                      "[" + ", ".join(f(x, 3) for x in e["primeras_a"]) + ", ...]", "[" + ", ".join(f(x, 3) for x in e["primeras_b"]) + ", ...]",
                      f(e["coseno"]), f(e["euclidiana"]), f(e["sim_euclidiana"])])
    w(tabla(["Modelo", "Dim", "Palabras con vector #%d" % ev["caso"]["a"], "Palabras con vector #%d" % ev["caso"]["b"], "Primeras 6 dim. #%d" % ev["caso"]["a"],
             "Primeras 6 dim. #%d" % ev["caso"]["b"], "Coseno", "Dist. euclidiana", "1/(1+d)"], filas))
    w("\nComo los vectores tienen norma 1, la distancia euclidiana cumple d^2 = 2 - 2 x coseno, por lo que ambas medidas ordenan los pares igual.\n")

    w("### 4.3 Analisis critico: clasicos frente a IA\n")
    w("**Resultados del caso de estudio y del contraste** (similitud normalizada [0,1]):\n")
    w(tabla(["Algoritmo", "Tipo", "Caso #%d-#%d (mas parecidos)" % (ev["caso"]["a"], ev["caso"]["b"]), "Contraste #%d-#%d (menos parecidos)" % tuple(ev["caso"]["contraste"]),
             "Posicion del caso entre 190 pares"],
            [[NOMBRES[k], "IA" if k.startswith("emb") else "Clasico", f(caso[k]), f(contr[k]), "%d de 190" % ev["posicion_caso"][k]] for k in CL], numericas=(2, 3)))
    w("\n**Comportamiento sobre los 190 pares** (minimo, maximo, promedio y rango de los puntajes):\n")
    w(tabla(["Algoritmo", "Minimo", "Maximo", "Promedio", "Rango", "Tiempo medio por par (ms)"],
            [[NOMBRES[k], f(ev["estadisticos"][k]["min"]), f(ev["estadisticos"][k]["max"]), f(ev["estadisticos"][k]["promedio"]), f(ev["estadisticos"][k]["rango"]),
              f(ev["tiempos_ms_por_par"][k]["promedio"], 3)] for k in CL], numericas=(1, 2, 3, 4, 5)))
    w("\n**Correlacion de Spearman entre algoritmos** (acuerdo en el *orden* de los 190 pares; 1 = mismo orden):\n")
    w(tabla([""] + [NOMBRES[k] for k in CL], [[NOMBRES[a]] + [f(ev["spearman"][a][b], 2) for b in CL] for a in CL], numericas=range(1, 7)))
    w("\n**Interpretacion (basada en las tablas anteriores).**\n")
    w("1. **Cada familia mide algo distinto.** Levenshtein y Needleman-Wunsch comparan la *secuencia de caracteres*: su acuerdo mutuo es alto (Spearman %s) pero con TF-IDF es bajo (%s y %s). "
      "TF-IDF y Jaccard comparan *vocabulario compartido* (acuerdo %s). Los embeddings comparan *cercania semantica aproximada*; su acuerdo con TF-IDF es moderado (GloVe %s, fastText %s).\n" % (
          f(ev["spearman"]["levenshtein"]["needleman-wunsch"], 2), f(ev["spearman"]["levenshtein"]["tfidf-coseno"], 2), f(ev["spearman"]["needleman-wunsch"]["tfidf-coseno"], 2),
          f(ev["spearman"]["tfidf-coseno"]["jaccard"], 2), f(ev["spearman"]["tfidf-coseno"]["emb-glove"], 2), f(ev["spearman"]["tfidf-coseno"]["emb-fasttext"], 2)))
    vf = ev["verif"]
    w("2. **Levenshtein y Needleman-Wunsch discriminan poco y dependen de la longitud.** Todos los pares caen en rangos estrechos (Levenshtein %s a %s; Needleman-Wunsch %s a %s). "
      "Se midio la relacion entre cada puntaje y la razon de longitudes de los textos limpios (min/max): la correlacion de Spearman es **%s** para Levenshtein y **%s** para Needleman-Wunsch, "
      "frente a **%s** para TF-IDF. Es decir, estos dos algoritmos ordenan los pares en buena medida segun cuanto difieren en longitud, no segun el tema. "
      "El signo negativo (a mayor diferencia de longitud, mayor similitud normalizada) es consistente con un artefacto de la normalizacion; no se investigo su mecanismo exacto. "
      "En el caso de estudio los textos miden %d y %d caracteres. Son medidas de *forma*, no de *significado*.\n" % (
          f(ev["estadisticos"]["levenshtein"]["min"], 3), f(ev["estadisticos"]["levenshtein"]["max"], 3), f(ev["estadisticos"]["needleman-wunsch"]["min"], 3), f(ev["estadisticos"]["needleman-wunsch"]["max"], 3),
          f(vf["spearman_lev_vs_razon_longitud"], 2), f(vf["spearman_nw_vs_razon_longitud"], 2), f(vf["spearman_tfidf_vs_razon_longitud"], 2), dpc["longitud_a"], dpc["longitud_b"]))
    w("3. **TF-IDF y Jaccard separan mejor** (TF-IDF: %s a %s). El caso de estudio sale 1.o en TF-IDF por construccion y %d.o en Jaccard: ponderar por IDF hace que terminos poco comunes como `aied` (df = 7) pesen mas que `educate` (df = 18). "
      "Limitacion: no ven sinonimos; \"learner\" y \"student\" son terminos distintos.\n" % (f(ev["estadisticos"]["tfidf-coseno"]["min"], 3), f(ev["estadisticos"]["tfidf-coseno"]["max"], 3), ev["posicion_caso"]["jaccard"]))
    eg, ef = vf["emb"]["glove"], vf["emb"]["fasttext"]
    w("4. **Los embeddings dan valores altos para casi todos los pares** (GloVe %s a %s; fastText %s a %s). Diagnostico medido: el coseno de cada abstract con el vector medio de los 20 abstracts es de %s en promedio (GloVe, minimo %s) y %s (fastText, minimo %s); "
      "es decir, todos los vectores comparten una direccion dominante, como era de esperar al promediar palabras de un mismo dominio. "
      "Si se resta esa media (diagnostico, no usado por la app), los cosenos entre pares pasan a abarcar de %s a %s (GloVe) y de %s a %s (fastText): el orden fino entre documentos existe, pero el valor crudo lo oculta. "
      "Por eso el par mas parecido por TF-IDF ocupa solo el puesto %d (GloVe) y %d (fastText) en su ranking y el par de contraste conserva %s y %s: **el valor absoluto no es comparable entre algoritmos; solo tiene sentido comparar el orden de los pares**.\n" % (
          f(ev["estadisticos"]["emb-glove"]["min"], 3), f(ev["estadisticos"]["emb-glove"]["max"], 3), f(ev["estadisticos"]["emb-fasttext"]["min"], 3), f(ev["estadisticos"]["emb-fasttext"]["max"], 3),
          f(eg["cos_medio_a_la_media"], 3), f(eg["cos_min_a_la_media"], 3), f(ef["cos_medio_a_la_media"], 3), f(ef["cos_min_a_la_media"], 3),
          f(eg["centrado_min"], 2), f(eg["centrado_max"], 2), f(ef["centrado_min"], 2), f(ef["centrado_max"], 2),
          ev["posicion_caso"]["emb-glove"], ev["posicion_caso"]["emb-fasttext"], f(contr["emb-glove"], 3), f(contr["emb-fasttext"], 3)))
    w("5. **Costo.** Levenshtein y Needleman-Wunsch cuestan ~%s ms por par (O(m*n)); TF-IDF, Jaccard y embeddings cuestan entre %s y %s ms. Los embeddings son baratos al consultar, pero su costo real esta en el calculo previo del vector "
      "(modelos de cientos de MB), que se hizo offline.\n" % (f(ev["tiempos_ms_por_par"]["levenshtein"]["promedio"], 0), f(ev["tiempos_ms_por_par"]["emb-glove"]["promedio"], 2), f(ev["tiempos_ms_por_par"]["jaccard"]["promedio"], 2)))
    w("6. **Conclusion.** Para *recuperar documentos que comparten terminologia* conviene TF-IDF; para *detectar cercania tematica general* los embeddings aportan una vision complementaria; "
      "para este corpus de abstracts, las medidas de edicion no son adecuadas como medida de similitud tematica, aunque son el ejemplo clasico de programacion dinamica. "
      "Los modelos de oraciones tipo Transformer (script opcional `generar_embeddings.py sbert`) podrian dar otro comportamiento, pero no se ejecutaron en este trabajo y por tanto no se reportan resultados ni se afirma que mejoren.\n")

    # ------------------------------------------------------------------ 5
    w("## 5. Requerimiento 2: clustering jerarquico\n")
    w("### 5.1 Explicacion tecnica\n")
    w("**Flujo:** abstracts -> preprocesamiento (con stemming) -> vectores TF-IDF -> matriz de distancias 20 x 20 (`1 - coseno`) -> fusiones sucesivas guardando el historial -> dendrograma dibujado con matplotlib a partir de ese historial (sin scipy).\n")
    w("**Algoritmo aglomerativo (`src/clustering.py::agrupar`):** empieza con 20 clusters de un documento; en cada paso fusiona el par de clusters mas cercano segun el criterio, "
      "registra `(a, b, distancia, tamano)` y repite hasta quedar uno solo (19 fusiones). Desempate determinista: menor distancia y luego menores identificadores.\n")
    w(tabla(["Criterio", "Distancia entre clusters A y B", "Tendencia"], [
        ["Single Linkage", "min d(a,b)", "Encadenamiento: une grupos por un solo par cercano; arboles alargados"],
        ["Complete Linkage", "max d(a,b)", "Grupos compactos de diametro parecido"],
        ["Average Linkage (UPGMA)", "promedio de todas las d(a,b)", "Compromiso entre ambos"],
    ]))
    w("\n**Complejidad:** tiempo O(n^3) y espacio O(n^2) en esta implementacion directa (n = 20 documentos; instantaneo).\n")
    w("**Metricas internas, implementadas a mano:** (1) *correlacion cofenetica*: Pearson entre las n(n-1)/2 distancias originales y las distancias cofeneticas (altura a la que dos documentos quedan por primera vez juntos); mas cerca de 1 = el arbol conserva mejor las distancias. "
      "(2) *silueta*: s(i) = (b - a)/max(a, b), con a = distancia media intra-grupo y b = menor distancia media a otro grupo, para un corte en k grupos.\n")
    w("**Verificacion contra scipy (solo en pruebas y en `generar_evidencias.py`, nunca en la app):** diferencia maxima de alturas de fusion = %s (single), %s (complete), %s (average); "
      "diferencia de correlacion cofenetica <= %s. Los resultados propios coinciden con los de scipy.\n" % (
          "%.1e" % ver["single"]["max_dif_alturas"], "%.1e" % ver["complete"]["max_dif_alturas"], "%.1e" % ver["average"]["max_dif_alturas"],
          "%.1e" % max(ver[k]["dif_ccc"] for k in ver)))

    w("### 5.2 Matriz de distancias y pasos de fusion\n")
    w("La matriz completa 20 x 20 esta en el Anexo B. Historial de fusiones de cada criterio (cluster `Cn` = n-esima fusion + 19; `#k` = articulo k):\n")
    for k in ("single", "complete", "average"):
        w("**%s** - alturas entre %s y %s\n" % (cc[k]["nombre"], f(cc[k]["altura_min"], 3), f(cc[k]["altura_max"], 3)))
        w(historial_md(cc[k]["historial"]))
        w("")
    w("### 5.3 Dendrogramas\n")
    for k in ("single", "complete", "average"):
        w("![Dendrograma %s](figuras/dendrograma_%s.png)\n" % (k, k))
    w("*(La linea roja es un corte en k = 4 grupos; el color de las etiquetas indica el grupo.)*\n")
    w("### 5.4 Evaluacion y conclusion\n")
    w(tabla(["Criterio", "Correlacion cofenetica", "Mejor k (silueta)", "Silueta en ese k", "Silueta con k = 4", "Ranking por CCC"],
            [[cc[k]["nombre"], f(cc[k]["ccc"]), cc[k]["mejor_k"], f(cc[k]["mejor_silueta"]), f(cc[k]["grupos"]["4"]["silueta"]), "%d" % (cla["ranking"].index(k) + 1)] for k in ("single", "complete", "average")],
            numericas=(1, 2, 3, 4, 5)))
    w("\n![Metricas de clustering](figuras/clustering_metricas.png)\n")
    g = {k: cc[k]["grupos"]["4"]["grupos"] for k in cc}
    w("**Grupos con k = 4:**\n")
    for k in ("single", "complete", "average"):
        w("- %s: %s" % (cc[k]["nombre"], " | ".join("{" + ", ".join("#%d" % i for i in gr) + "}" for gr in g[k])))
    w("")
    w("**Conclusion.** El criterio mas coherente es **%s**, con la mayor correlacion cofenetica (%s frente a %s de Single y %s de Complete): su arbol reproduce mejor las distancias originales entre abstracts. "
      "Single muestra el encadenamiento esperado: con k = 4 deja tres documentos aislados y un grupo gigante de %d articulos (silueta %s), poco informativo. "
      "Complete forma grupos mas equilibrados (tamanos %s) y tiene la silueta mas alta con k = 4 (%s), pero su arbol distorsiona mas las distancias (CCC mas baja). "
      "Average combina ambas ventajas razonablemente. **Salvedad honesta:** la silueta es baja en los tres criterios (maximo %s), lo que indica que los abstracts, al ser del mismo dominio y de poca longitud, "
      "forman una nube con pocos grupos nitidamente separados; por eso la silueta se usa como criterio de apoyo y la decision se sustenta en la correlacion cofenetica. "
      "A modo de lectura tematica, en Complete aparece un grupo con los articulos sobre IA generativa y evaluacion (#11, #13, #16, #17, #18 y #19) y otro con las revisiones generales de IA en educacion (#2, #5, #6, #7, #9, #12 y #20), "
      "coherente con sus titulos.\n" % (
          cc[mejor]["nombre"], f(cc[mejor]["ccc"]), f(cc["single"]["ccc"]), f(cc["complete"]["ccc"]), max(len(x) for x in g["single"]),
          f(cc["single"]["grupos"]["4"]["silueta"]), ", ".join(str(len(x)) for x in g["complete"]), f(cc["complete"]["grupos"]["4"]["silueta"]),
          f(max(cc[k]["mejor_silueta"] for k in cc))))

    # ------------------------------------------------------------------ 6
    w("## 6. Requerimiento 3: busqueda de patrones\n")
    w("### 6.1 Explicacion tecnica\n")
    w("La app recibe un patron, lo busca en el abstract de los 20 articulos y muestra documento, posicion (base 0) y fragmento resaltado. "
      "Los tres algoritmos se implementan con indices y bucles (sin `find`, `index`, `in`, `replace` ni regex) y devuelven **todas** las ocurrencias, incluidas las superpuestas. "
      "Por defecto no distingue mayusculas: se compara texto y patron convertidos con `a_minusculas`, que conserva la longitud y por eso las posiciones sirven para el texto original. "
      "Entradas invalidas (patron vacio o de mas de 200 caracteres, texto no cadena, algoritmo desconocido) lanzan `ErrorPatron`; un patron mas largo que el texto devuelve cero ocurrencias.\n")
    w(tabla(["Algoritmo", "Preprocesamiento", "Busqueda: mejor", "Busqueda: promedio", "Busqueda: peor", "Espacio"], [
        ["KMP", "O(m) (tabla LPS)", "O(n)", "O(n)", "O(n)", "O(m)"],
        ["Boyer-Moore (caracter malo + sufijo bueno)", "O(m + s), s = alfabeto", "O(n/m)", "~O(n)", "O(n*m) (muchas ocurrencias; no se implemento la regla de Galil)", "O(m + s)"],
        ["Rabin-Karp", "O(m)", "O(n + m)", "O(n + m)", "O(n*m) (colisiones o hashes iguales siempre)", "O(1)"],
    ]))
    w("")
    w("### 6.2 Caso de estudio\n")
    w("**Patron:** `%s` (m = %d). Se eligio porque su tabla LPS **no es trivial** (tiene un borde `pe`) y aparece en el corpus (5 veces; 2 de ellas en el abstract #%d). "
      "**Texto:** el abstract #%d completo (n = %d caracteres), *%s*. Ocurrencias encontradas por los tres algoritmos: posiciones **%s**.\n\n> %s\n" % (
          pt["patron"], pt["m"], pt["doc"], pt["doc"], pt["n"], pt["titulo_doc"], " y ".join(str(x) for x in pt["algoritmos"]["kmp"]["posiciones"]), pt["texto"]))
    w("#### 6.2.1 KMP: tabla LPS\n")
    p = pt["patron"]
    w("`lps[i]` = longitud del prefijo propio mas largo de `P[0..i]` que tambien es sufijo. `lps[4] = 1` porque `p` (P[4]) coincide con `p` (P[0]); `lps[5] = 2` porque `pe` (P[4..5]) coincide con `pe` (P[0..1]).\n")
    w(tabla(["i"] + [str(i) for i in range(len(p))], [["P[i]"] + list(p), ["lps[i]"] + [str(x) for x in pt["lps"]]]))
    a = pt["algoritmos"]["kmp"]
    w("\nEn una falla despues de emparejar j caracteres, el patron se desplaza usando `j = lps[j-1]` y **el texto nunca retrocede**. Resultado sobre el abstract: %d comparaciones con n = %d (KMP hace como maximo 2n comparaciones).\n" % (a["comparaciones"], pt["n"]))
    w("![Iteraciones KMP](figuras/patron_kmp.png)\n")
    w("#### 6.2.2 Boyer-Moore: tablas heuristicas\n")
    w("**Tabla del caracter malo** (ultima posicion de cada caracter en el patron; los caracteres que no estan valen -1):\n")
    claves = sorted(pt["malo"])
    w(tabla(["Caracter"] + claves, [["ultima posicion"] + [str(pt["malo"][k]) for k in claves]]))
    w("\n**Tabla del sufijo bueno** `shift[k]`: avance cuando la comparacion falla en la posicion j = k - 1 habiendo coincidido ya el sufijo P[k..m-1]; `shift[0]` es el avance tras una coincidencia completa. `borde[k]` es la tabla auxiliar de bordes con la que se construye:\n")
    w(tabla(["k"] + [str(i) for i in range(len(pt["bueno"]))], [["shift[k]"] + [str(x) for x in pt["bueno"]], ["borde[k]"] + [str(x) for x in pt["borde"]]]))
    b = pt["algoritmos"]["boyer-moore"]
    w("\nSe compara de derecha a izquierda y, ante una falla en la posicion j con el caracter `c` del texto, el patron avanza `max(j - ultima[c], shift[j+1])`. "
      "Sobre el abstract hubo %d alineamientos y %d comparaciones (frente a n = %d caracteres): Boyer-Moore **salta** gran parte del texto.\n" % (b["iteraciones"], b["comparaciones"], pt["n"]))
    w("Primeras iteraciones reales:\n")
    w(tabla(["Alineamiento s", "Falla en j", "Caracter del texto", "Desp. caracter malo", "Desp. sufijo bueno", "Regla usada", "Avance"],
            [[e["s"], e["j"], "`%s`" % e.get("caracter_texto", "-"), e["malo"], e["bueno"], e["regla"], e["desplazamiento"]] for e in b["traza_inicio"][:8]], numericas=(0, 1, 3, 4, 6)))
    w("\n![Iteraciones Boyer-Moore](figuras/patron_boyer_moore.png)\n")
    w("#### 6.2.3 Rabin-Karp: hash inicial, hash rodante y colisiones\n")
    w("Se usa el hash polinomial `h = (c0*B^(m-1) + c1*B^(m-2) + ... + c(m-1)) mod q` con base B = %d y modulo q = %d (primo). Valores ASCII del patron: %s.\n" % (
        rk["base"], rk["modulo"], ", ".join("`%s`=%d" % (t["c"], t["ord"]) for t in rk["terminos_horner"])))
    w("**Hash del patron** (Horner) = **%d**. **B^(m-1) mod q** = %d. **Hash de la primera ventana** `%s` = **%d**.\n" % (rk["hash_patron"], rk["potencia"], rk["ventana0"], rk["hash_primera_ventana"]))
    w("**Hash rodante:** `h(s+1) = ((h(s) - T[s] * B^(m-1)) * B + T[s+m]) mod q`. Verificacion numerica de las primeras ventanas contra el calculo directo:\n")
    w(tabla(["s", "hash de la ventana s", "sale", "entra", "hash rodante s+1", "hash directo s+1", "coinciden"],
            [[r["s"], r["hash_ventana"], "`%s`" % r["saliente"], "`%s`" % r["entrante"], r["hash_siguiente"], r["directo"], "si" if r["hash_siguiente"] == r["directo"] else "NO"] for r in rk["rodante"]], numericas=(0, 1, 4, 5)))
    w("\n**Colisiones.** Cuando el hash de una ventana es igual al del patron se verifica caracter por caracter: si no es igual, es una *colision* (falso positivo). Efecto del modulo sobre este mismo texto (%d ventanas):\n" % pt["colisiones_por_modulo"][0]["ventanas"])
    w(tabla(["Modulo q", "Hash del patron", "Colisiones", "Ocurrencias reales"], [[x["modulo"], x["hash_patron"], x["colisiones"], len(x["posiciones"])] for x in pt["colisiones_por_modulo"]], numericas=(0, 1, 2, 3)))
    w("\nCon q = %d (demostracion) el hash del patron es %d y hay %d colisiones reales; ejemplos:\n" % (rkd["modulo"], rkd["hash_patron"], rkd["colisiones"]))
    w(tabla(["Posicion s", "Ventana", "Hash", "Hash del patron", "Resultado"], [[e["s"], "`%s`" % e["ventana"], e["hash"], e["hash_patron"], "colision (los caracteres no coinciden)"] for e in rkd["colisiones_detalle"][:5]], numericas=(0, 2, 3)))
    w("\nEn todos los casos el resultado final fue correcto (posiciones %s), porque cada coincidencia de hash se verifica. Con el modulo grande no hubo colisiones.\n" % " y ".join(str(x) for x in rkd["posiciones"]))
    w("![Iteraciones Rabin-Karp](figuras/patron_rabin_karp.png)\n")
    w("*(Las graficas muestran un fragmento centrado en la primera ocurrencia: barras = alineamiento del patron; flechas = desplazamiento; verde = ocurrencia; gris = ventana sin coincidencia.)*\n")

    w("### 6.3 Analisis critico: Big O teorica frente a tiempos reales\n")
    w("**Corpus completo** (n = %d caracteres, mediana de 15 corridas; tiempos de preprocesamiento y de busqueda por separado):\n" % bm["n_corpus"])
    filas = []
    for it in bm["por_patron"]:
        r = it["resultado"]
        for a_ in ("kmp", "boyer-moore", "rabin-karp"):
            filas.append([it["patron"], it["m"], a_, f(r[a_]["ms_preprocesamiento"], 4), f(r[a_]["ms_busqueda"], 2), r[a_]["comparaciones"], r[a_]["ocurrencias"]])
    w(tabla(["Patron", "m", "Algoritmo", "Preproc. (ms)", "Busqueda (ms)", "Comparaciones", "Ocurrencias"], filas, numericas=(1, 3, 4, 5, 6)))
    w("\n![Tiempos sobre el corpus](figuras/tiempos_corpus.png)\n")
    w("**Escalabilidad:** el corpus se repite k veces (patron `%s`). Si la busqueda es lineal, el tiempo debe crecer proporcional a n.\n" % pt["patron"])
    filas = []
    for fr in esc:
        r = fr["algoritmos"]
        filas.append([fr["factor"], fr["n"], f(r["kmp"]["ms_busqueda"], 1), f(r["boyer-moore"]["ms_busqueda"], 1), f(r["rabin-karp"]["ms_busqueda"], 1)])
    w(tabla(["k", "n (caracteres)", "KMP (ms)", "Boyer-Moore (ms)", "Rabin-Karp (ms)"], filas, numericas=(0, 1, 2, 3, 4)))
    e0, e1 = esc[0], esc[-1]
    w("\nAl multiplicar n por %d, el tiempo se multiplico por %s (KMP), %s (Boyer-Moore) y %s (Rabin-Karp): **crecimiento lineal**, como predice O(n).\n" % (
        e1["factor"], f(e1["algoritmos"]["kmp"]["ms_busqueda"] / e0["algoritmos"]["kmp"]["ms_busqueda"], 1),
        f(e1["algoritmos"]["boyer-moore"]["ms_busqueda"] / e0["algoritmos"]["boyer-moore"]["ms_busqueda"], 1),
        f(e1["algoritmos"]["rabin-karp"]["ms_busqueda"] / e0["algoritmos"]["rabin-karp"]["ms_busqueda"], 1)))
    w("![Escalabilidad](figuras/escalabilidad.png)\n")
    w("**Casos limite sinteticos** (n = %d, m = %d; textos artificiales, no del corpus):\n" % (sint[0]["n"], sint[0]["m"]))
    filas = []
    for s_ in sint:
        r = s_["algoritmos"]
        filas.append([s_["caso"]] + ["%s ms / %d comp." % (f(r[a_]["ms_busqueda"], 1), r[a_]["comparaciones"]) for a_ in ("kmp", "boyer-moore", "rabin-karp")])
    w(tabla(["Caso", "KMP", "Boyer-Moore", "Rabin-Karp"], filas))
    s0, s2 = sint[0]["algoritmos"], sint[2]["algoritmos"]
    w("\n**Lectura.**\n")
    w("1. **Boyer-Moore, mejor caso:** sin ocurrencias y con un alfabeto distinto, hizo %d comparaciones = n/m = %d, frente a %d de KMP: salta de m en m. En el corpus real, con m = 12 hizo %d comparaciones frente a %d de KMP.\n" % (
        s0["boyer-moore"]["comparaciones"], sint[0]["n"] // sint[0]["m"], s0["kmp"]["comparaciones"], bm["por_patron"][2]["resultado"]["boyer-moore"]["comparaciones"], bm["por_patron"][2]["resultado"]["kmp"]["comparaciones"]))
    w("2. **Peor caso O(n*m):** con el patron a^m sobre a^n, Boyer-Moore y Rabin-Karp hicieron %d comparaciones (= (n - m + 1) x m = %d), mientras KMP se mantuvo en %d (lineal). "
      "El tiempo lo confirma: %s ms (Boyer-Moore) y %s ms (Rabin-Karp) frente a %s ms (KMP).\n" % (
          s2["boyer-moore"]["comparaciones"], (sint[2]["n"] - sint[2]["m"] + 1) * sint[2]["m"], s2["kmp"]["comparaciones"],
          f(s2["boyer-moore"]["ms_busqueda"], 1), f(s2["rabin-karp"]["ms_busqueda"], 1), f(s2["kmp"]["ms_busqueda"], 1)))
    pb = bm["por_patron"][2]["resultado"]
    w("3. **Preprocesamiento frente a busqueda:** el preprocesamiento es despreciable (%s ms KMP, %s ms Boyer-Moore, %s ms Rabin-Karp) frente a la busqueda (%s, %s y %s ms) porque el patron mide 12 caracteres y el texto %d. "
      "Boyer-Moore paga el preprocesamiento mas caro (dos tablas, O(m + s)) pero lo recupera al saltar.\n" % (
          f(pb["kmp"]["ms_preprocesamiento"], 4), f(pb["boyer-moore"]["ms_preprocesamiento"], 4), f(pb["rabin-karp"]["ms_preprocesamiento"], 4),
          f(pb["kmp"]["ms_busqueda"], 2), f(pb["boyer-moore"]["ms_busqueda"], 2), f(pb["rabin-karp"]["ms_busqueda"], 2), bm["n_corpus"]))
    w("4. **Rabin-Karp hace menos comparaciones de caracteres pero es el mas lento en Python** (%s ms frente a %s de KMP): hace muy pocas comparaciones (solo verifica coincidencias de hash), pero actualiza un hash con multiplicaciones y modulo en cada ventana. "
      "El conteo de comparaciones no es el unico factor: el costo por operacion tambien importa. Con patrones muy cortos (`ai`, m = 2) Boyer-Moore pierde su ventaja porque los saltos son minimos.\n" % (
          f(pb["rabin-karp"]["ms_busqueda"], 2), f(pb["kmp"]["ms_busqueda"], 2)))
    w("5. Los tiempos absolutos dependen de la maquina (aqui %s CPU, Python %s) y del lenguaje; lo que se contrasta con la teoria es la **forma de crecimiento y el numero de comparaciones**, que si son independientes de la maquina.\n" % (maq["cpus"], maq["python"]))

    # ------------------------------------------------------------------ 7
    w("## 7. Despliegue, pruebas y calidad\n")
    w("**Despliegue (Render).** `Procfile`: `web: gunicorn src.api:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`. `render.yaml` describe el servicio (plan gratuito, `pip install -r requirements.txt`). "
      "`requirements.txt` solo contiene Flask, matplotlib y gunicorn. Los datos (`data/processed/*.json`, ~%s KB) viajan en el repositorio; los PDFs y los modelos de embeddings **no**. "
      "Las rutas se configuran con `BIBLIO_DATA_DIR`/`BIBLIO_REPORTS_DIR` y, si no se puede escribir, se usa una carpeta temporal. Pasos exactos en `README.md`.\n" % _kb_datos())
    w("**Pruebas (`pytest`).** Casos conocidos (por ejemplo `Levenshtein(kitten, sitting) = 3`; Needleman-Wunsch GATTACA/GCATGCU = 0; LPS de `ABABCABAB`), "
      "calculo a mano de TF-IDF y de las tres alturas de enlace, contraste del clustering con scipy, 2.500 casos aleatorios donde KMP, Boyer-Moore y Rabin-Karp coinciden con una referencia independiente, "
      "tabla del sufijo bueno contra su definicion, colisiones de Rabin-Karp con modulo pequeno, y manejo de errores: PDF sin abstract, entradas vacias, patron mas largo que el texto, articulo inexistente, "
      "menos de dos articulos, API con JSON invalido.\n")
    w("**Limites de la web:** de 2 a 6 articulos por comparacion y patrones de hasta 200 caracteres.\n")

    # ------------------------------------------------------------------ 8
    w("## 8. Conclusiones\n")
    w("- Se implemento desde cero toda la logica algoritmica pedida y se verifico con pruebas y, solo en pruebas, contra scipy.\n"
      "- **Similitud:** ninguna medida es \"la mejor\": miden forma, vocabulario o significado aproximado. En este corpus, TF-IDF discrimina mejor; Levenshtein y Needleman-Wunsch casi no distinguen temas; los embeddings promediados comprimen los valores hacia arriba.\n"
      "- **Clustering:** Average Linkage es el criterio mas coherente por correlacion cofenetica (%s); la silueta baja en los tres refleja un corpus homogeneo.\n"
      "- **Patrones:** los tres algoritmos devuelven exactamente las mismas posiciones; los tiempos crecen linealmente con n y el peor caso O(n*m) de Boyer-Moore y Rabin-Karp se observo de forma directa en las comparaciones.\n" % f(cc[mejor]["ccc"]))
    w("## 9. Limitaciones y trabajo futuro\n")
    w("- Solo se procesan 20 abstracts en ingles; el stemming es simple (reglas de sufijos) y puede unir o separar formas incorrectamente (por ejemplo `series` -> `sery`).\n"
      "- Los embeddings son promedios de vectores de palabras estaticos: pierden orden y contexto. Trabajo futuro: modelos de oraciones tipo Transformer (script opcional incluido pero **no ejecutado**), ponderar el promedio con IDF y restar la componente comun (el diagnostico de la seccion 4.3 sugiere que ayudaria, pero no se evaluo como metodo).\n"
      "- La silueta es baja; un corpus mayor o abstracts mas diversos permitirian grupos mas separados. Falta probar el criterio de Ward con distancias euclidianas.\n"
      "- Boyer-Moore no incluye la regla de Galil (peor caso O(n*m) con muchas ocurrencias). Posible extension: Aho-Corasick para varios patrones y busqueda aproximada.\n"
      "- El plan gratuito de Render duerme tras inactividad: la primera consulta puede tardar; Levenshtein/Needleman-Wunsch con 6 articulos (15 pares) son los calculos mas pesados.\n"
      "- Los tiempos reportados corresponden a una sola maquina; deben repetirse en el equipo del grupo para la sustentacion.\n")

    # ------------------------------------------------------------------ 10
    w("## 10. Declaracion de uso de IA generativa\n")
    w("> **Borrador redactado por la herramienta de IA; el grupo debe leerlo y ajustarlo a lo que realmente hizo cada integrante antes de entregarlo.**\n")
    w("Se utilizo **Claude (Anthropic)** como asistente de desarrollo durante el proyecto. Su aporte fue de **apoyo**:\n"
      "- Genero borradores de codigo (implementacion de los algoritmos, API, interfaz web), pruebas unitarias y la redaccion inicial de la documentacion, a partir de los requerimientos y decisiones indicados por el grupo (por ejemplo, la eleccion de modelos de embeddings, criterios de enlace y estructura del repositorio).\n"
      "- Ejecuto el codigo en su entorno para producir las evidencias numericas, figuras y tablas del documento; ninguna cifra se escribio a mano.\n"
      "- Los modelos preentrenados de embeddings (GloVe y fastText) son modelos de terceros usados como insumo, descritos en la seccion 4.\n\n"
      "**Lo que la IA no reemplaza:** el grupo es responsable de comprender cada algoritmo (formulas, complejidad y casos de estudio), de revisar y ejecutar el codigo, de verificar los resultados "
      "(las pruebas y la comparacion con scipy estan en el repositorio) y de sustentarlos. La *Guia de sustentacion* incluye explicaciones y ejemplos manuales para ese fin. "
      "Las referencias bibliograficas se incluyeron de memoria del asistente: **deben verificarse** contra las fuentes originales antes de la entrega.\n")

    # ------------------------------------------------------------------ 11
    w("## 11. Referencias\n")
    w("*(Citadas de memoria; verificar volumen, paginas y anio en las fuentes originales.)*\n")
    for r in [
        "V. I. Levenshtein, \"Binary codes capable of correcting deletions, insertions and reversals\", *Soviet Physics Doklady*, 10(8), 707-710, 1966.",
        "S. B. Needleman y C. D. Wunsch, \"A general method applicable to the search for similarities in the amino acid sequence of two proteins\", *Journal of Molecular Biology*, 48(3), 443-453, 1970.",
        "P. Jaccard, \"Distribution de la flore alpine dans le bassin des Dranses et dans quelques regions voisines\", *Bulletin de la Societe Vaudoise des Sciences Naturelles*, 37, 241-272, 1901.",
        "G. Salton y C. Buckley, \"Term-weighting approaches in automatic text retrieval\", *Information Processing & Management*, 24(5), 513-523, 1988.",
        "D. E. Knuth, J. H. Morris y V. R. Pratt, \"Fast pattern matching in strings\", *SIAM Journal on Computing*, 6(2), 323-350, 1977.",
        "R. S. Boyer y J. S. Moore, \"A fast string searching algorithm\", *Communications of the ACM*, 20(10), 762-772, 1977.",
        "R. M. Karp y M. O. Rabin, \"Efficient randomized pattern-matching algorithms\", *IBM Journal of Research and Development*, 31(2), 249-260, 1987.",
        "R. R. Sokal y C. D. Michener, \"A statistical method for evaluating systematic relationships\", *University of Kansas Science Bulletin*, 38, 1409-1438, 1958.",
        "R. R. Sokal y F. J. Rohlf, \"The comparison of dendrograms by objective methods\", *Taxon*, 11(2), 33-40, 1962.",
        "P. J. Rousseeuw, \"Silhouettes: a graphical aid to the interpretation and validation of cluster analysis\", *Journal of Computational and Applied Mathematics*, 20, 53-65, 1987.",
        "J. Pennington, R. Socher y C. D. Manning, \"GloVe: Global vectors for word representation\", *Proc. EMNLP*, 1532-1543, 2014.",
        "T. Mikolov, E. Grave, P. Bojanowski, C. Puhrsch y A. Joulin, \"Advances in pre-training distributed word representations\", *Proc. LREC*, 2018.",
        "T. H. Cormen, C. E. Leiserson, R. L. Rivest y C. Stein, *Introduction to Algorithms*, MIT Press (capitulos de programacion dinamica y de coincidencia de cadenas).",
    ]:
        w("- " + r)
    w("\n**Corpus analizado (20 articulos):**\n")
    for a_ in c["articulos"]:
        w("%d. %s. *%s*." % (a_["id"], ", ".join(a_["autores"]), a_["titulo"]))

    # ------------------------------------------------------------------ anexos
    w("\n## Anexo A. Tabla completa de terminos TF-IDF del caso de estudio (#%d y #%d)\n" % (ev["caso"]["a"], ev["caso"]["b"]))
    w("Ordenados por aporte al producto punto. N = 20; IDF = ln(21/(1+df)) + 1.\n")
    w(tabla(["Termino", "df", "IDF", "TF A", "TF B", "w A", "w B", "w A x w B"],
            [[t["termino"], t["df"], f(t["idf"], 3), f(t["tf_a"]), f(t["tf_b"]), f(t["w_a"]), f(t["w_b"]), f(t["producto"], 5)] for t in tf["terminos_mayor_aporte"]],
            numericas=(1, 2, 3, 4, 5, 6, 7)))
    w("\n## Anexo B. Matriz de distancias (1 - coseno TF-IDF) entre los 20 abstracts\n")
    D = cla["distancias"]
    for ini, fin, nombre in ((0, 10, "columnas #1 a #10"), (10, 20, "columnas #11 a #20")):
        w("*Bloque: %s*\n" % nombre)
        w(tabla([""] + ["#%d" % cla["ids"][j] for j in range(ini, fin)], [["#%d" % cla["ids"][i]] + [f(D[i][j], 3) for j in range(ini, fin)] for i in range(20)],
                numericas=range(1, fin - ini + 1)))
        w("")
    w("\n## Anexo C. Top 5 de pares mas parecidos por algoritmo\n")
    for k in CL:
        w("**%s:** %s\n" % (NOMBRES[k], "; ".join("#%d-#%d (%s)" % (a_, b_, f(s_, 3)) for a_, b_, s_ in ev["top5"][k])))
    return "\n".join(L) + "\n"
