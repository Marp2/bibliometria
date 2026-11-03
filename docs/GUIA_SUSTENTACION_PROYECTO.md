# Guia de sustentacion

Objetivo: que cada integrante pueda explicar **cada linea** y responder al profesor. Lea primero la secuencia de demostracion y luego las preguntas.

## 1. Secuencia de demostracion (10 minutos)

1. **Corpus** (`/ui/corpus`): 20/20 abstracts validados; abrir el #14 y explicar la cita pegada en el PDF original; mostrar el preprocesamiento paso a paso.
2. **Similitud** (`/ui/similarity`): elegir #2 y #6, comparar, abrir *Ver calculo detallado* (producto punto, normas, angulo) y la matriz de calor.
3. **Clustering** (`/ui/clustering`): tabla de metricas, dendrograma de cada criterio, cambiar k y ver los grupos.
4. **Patrones** (`/ui/patterns`): buscar `perspectives`, ver las posiciones, *Iteraciones* de los tres algoritmos y *Medir tiempos*.
5. **Pruebas:** `python -m pytest -q` en vivo.

## 2. Que debe saber explicar cada uno

| Tema | Una frase | Donde mirar el codigo |
|--------------------|----------------------------------------------------------------------|--------------------------------------------------|
| Levenshtein | Minimo de inserciones/borrados/sustituciones; tabla de programacion dinamica O(m*n) | `levenshtein_matriz` |
| Needleman-Wunsch | Igual que Levenshtein pero maximiza puntaje (+1, -1, -1) y permite recuperar el alineamiento | `needleman_wunsch_alineamiento` |
| TF-IDF + coseno | Peso = frecuencia en el documento x rareza en el corpus; coseno = angulo entre vectores | `vector_tfidf`, `coseno_vectores` |
| Jaccard | Terminos compartidos / terminos totales | `jaccard` |
| Embeddings | Vectores densos de palabras preentrenados; promedio por abstract; coseno y euclidiana a mano | `similitud_embeddings.py`, `generar_embeddings.py` |
| Clustering | Fusionar siempre los dos clusters mas cercanos; el criterio define 'cercano' (min, max, promedio) | `agrupar` |
| Cofenetica y silueta | Fidelidad del arbol a las distancias; cohesion frente a separacion de los grupos | `correlacion_cofenetica`, `silueta` |
| KMP | Tabla LPS evita retroceder en el texto | `kmp_tabla_lps`, `kmp_buscar` |
| Boyer-Moore | Compara de derecha a izquierda y salta con caracter malo y sufijo bueno | `bm_buscar` |
| Rabin-Karp | Compara hashes rodantes y verifica; las colisiones son falsos positivos | `rk_buscar` |


## 3. Preguntas tipicas del profesor y respuestas cortas

**1. Por que no uso scipy ni sklearn?**  
El enunciado exige implementar los algoritmos explicitamente. scipy solo aparece en las pruebas para verificar que mis alturas de fusion y mi correlacion cofenetica coinciden.

**2. Por que los embeddings no se calculan en la web?**  
Los modelos pesan cientos de MB; no caben en el plan gratuito de Render. Se calculan una vez con `generar_embeddings.py` y la app lee `embeddings_*.json`.

**3. Que modelos de embeddings usaron y como obtienen el vector del abstract?**  
GloVe y fastText de 300 dimensiones. El vector es el promedio de los vectores de las palabras del abstract (sin stopwords), normalizado. No son modelos Transformer.

**4. Por que los embeddings dan 0,9 para casi todo?**  
Todos los abstracts comparten un vector dominante (el coseno de cada uno con la media del corpus es de al menos 0.92 en GloVe y 0.97 en fastText). Solo es util comparar el orden de los pares, no el valor absoluto.

**5. Por que Levenshtein da valores parecidos para todos los pares?**  
Mide la forma de la cadena; medimos que su orden depende de la razon de longitudes (Spearman -0.80). No mide tema.

**6. Cual es la complejidad de Levenshtein y como se reduce el espacio?**  
O(m*n) en tiempo; con dos filas el espacio baja de O(m*n) a O(min(m,n)).

**7. Que es el IDF suavizado y por que?**  
ln((1+N)/(1+df)) + 1. Evita que un termino presente en todos los documentos tenga peso 0 y evita dividir por cero.

**8. Como normalizan Needleman-Wunsch a [0,1]?**  
(puntaje - minimo)/(maximo - minimo), con maximo = min(m,n) - |m-n| y minimo = -(m+n), las cotas teoricas con +1/-1/-1.

**9. Por que Average y no Ward?**  
El enunciado pide tres criterios; Ward requiere distancias euclidianas y aqui la distancia natural es 1 - coseno.

**10. Por que Average es el mejor?**  
Mayor correlacion cofenetica: 0.803 frente a 0.733 (Single) y 0.707 (Complete).

**11. La silueta es muy baja; eso invalida el resultado?**  
No, indica que los abstracts forman una nube homogenea y sin grupos nitidos (maximo 0.069). Por eso la decision se apoya en la cofenetica y lo declaramos.

**12. Que es el encadenamiento de Single?**  
Single une grupos por un solo par cercano; con k = 4 deja tres documentos aislados y un grupo grande. Se ve en el dendrograma como una escalera.

**13. Cual es la complejidad de su clustering?**  
O(n^3) tiempo y O(n^2) espacio; con n = 20 es instantaneo. Existen versiones O(n^2) con actualizacion de distancias, pero esta deja la definicion de cada criterio a la vista.

**14. Como se dibuja el dendrograma sin scipy?**  
`coordenadas_dendrograma` convierte el historial en segmentos (x1,y1,x2,y2): dos verticales hasta la altura de fusion y una horizontal que las une.

**15. Que tabla usa KMP y por que no retrocede?**  
La tabla LPS (prefijo que tambien es sufijo). Ante una falla, el patron salta a lps[j-1] y el indice del texto nunca baja; por eso O(n).

**16. Cual es la complejidad de Boyer-Moore?**  
Preprocesamiento O(m + s); busqueda mejor O(n/m), promedio ~O(n), peor O(n*m). Lo medimos: con todas las posiciones coincidiendo hizo 798440 comparaciones frente a 20000 de KMP.

**17. Por que usan caracter malo Y sufijo bueno?**  
El enunciado permite uno o ambos; el avance es el maximo de los dos, y el sufijo bueno compensa los casos donde el caracter malo daria avances pequenos.

**18. Que es una colision en Rabin-Karp?**  
Dos cadenas distintas con el mismo hash. Por eso cada coincidencia de hash se verifica caracter por caracter. Con modulo 101 hubo 13 colisiones; con el primo grande, 0.

**19. Como funciona el hash rodante?**  
h(s+1) = ((h(s) - T[s]*B^(m-1))*B + T[s+m]) mod q: quita el caracter que sale y agrega el que entra en O(1).

**20. Por que Rabin-Karp es el mas lento si hace menos comparaciones?**  
Porque en cada ventana hace multiplicaciones y modulo; el conteo de comparaciones de caracteres no es el unico costo.

**21. Como saben que los tres algoritmos coinciden?**  
`comparar_algoritmos` los corre sobre el corpus y verifica igualdad de posiciones; ademas hay 2.500 casos aleatorios contra una referencia independiente en `tests/test_patrones.py`.

**22. Que hacen con mayusculas y posiciones?**  
Por defecto no distingue mayusculas: convierte texto y patron con `a_minusculas`, que conserva la longitud, asi las posiciones valen para el texto original.

**23. Que pasa con entradas invalidas?**  
Patron vacio o de mas de 200 caracteres, texto no cadena o algoritmo desconocido -> `ErrorPatron` (HTTP 400). Patron mas largo que el texto -> 0 ocurrencias. Articulo inexistente -> 404.

**24. Por que Needleman-Wunsch y Levenshtein tardan?**  
Recorren matrices de cientos x cientos de celdas por par (unos 185 ms por par en nuestras mediciones); por eso la web limita la comparacion a 6 articulos.

**25. Que uso hicieron de IA generativa?**  
Esta declarado en la seccion 10 del documento tecnico: apoyo en codigo, pruebas y redaccion; nosotros revisamos, ejecutamos y sustentamos. Ajusten esa seccion a lo que realmente hizo cada uno.

**26. Que limitaciones tiene el trabajo?**  
20 abstracts en ingles; stemming simple; embeddings promediados (no Transformer); silueta baja; tiempos medidos en una sola maquina.

## 4. Ejercicios manuales para practicar

1. Llenar a mano la matriz de Levenshtein de `gato` y `pato` (resultado 1).
2. Calcular la tabla LPS de `ABAB` (`[0,0,1,2]`) y de `AABAA` (`[0,1,0,1,2]`).
3. Con puntos 0, 1, 5, 7, hacer Single, Complete y Average (alturas en `tests/test_clustering.py`).
4. Con TF-IDF, dados df y conteos, calcular IDF suavizado de un termino con N = 20.

## 5. Cosas que NO decir

- "Los embeddings entienden el significado": son promedios de vectores de palabras y comprimen las diferencias.
- "Average es el mejor" sin mencionar que la silueta es baja.
- Cifras de tiempo como absolutas: dependen de la maquina; lo que importa es la forma de crecimiento y el conteo de comparaciones.

