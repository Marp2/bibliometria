/* Logica compartida del frontend. Cada pagina declara <body data-page="..."> y aqui se activa su modulo. */
"use strict";

const $ = (s, r = document) => r.querySelector(s);

/** Crea un elemento DOM de forma segura (los textos se insertan con textContent, nunca como HTML). */
function h(tag, attrs = {}, ...hijos) {
  const e = document.createElement(tag);
  for (const k of Object.keys(attrs || {})) {
    if (k === "class") e.className = attrs[k];
    else if (k === "onclick") e.addEventListener("click", attrs[k]);
    else if (k === "onchange") e.addEventListener("change", attrs[k]);
    else if (attrs[k] !== false && attrs[k] !== null && attrs[k] !== undefined) e.setAttribute(k, attrs[k]);
  }
  for (const c of hijos.flat()) {
    if (c === null || c === undefined || c === false) continue;
    e.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return e;
}
const vaciar = (e) => { while (e.firstChild) e.removeChild(e.firstChild); return e; };
const fmt = (x, d = 3) => (x === null || x === undefined || Number.isNaN(x)) ? "-" : Number(x).toFixed(d);
const ms = (x) => (x < 1 ? x.toFixed(3) : x.toFixed(2)) + " ms";

async function api(url, opciones) {
  let r;
  try { r = await fetch(url, opciones); } catch (e) { throw new Error("No se pudo conectar con el servidor."); }
  const tipo = r.headers.get("content-type") || "";
  const datos = tipo.includes("json") ? await r.json() : null;
  if (!r.ok) throw new Error((datos && datos.detail) || ("Error " + r.status));
  return datos;
}
function estado(sel, msg, tipo = "") {
  const e = $(sel); if (!e) return;
  e.className = "status " + tipo; e.textContent = msg; e.hidden = !msg;
}
function tabla(cabeceras, filas, opciones = {}) {
  const t = h("table", {}, h("thead", {}, h("tr", {}, cabeceras.map((c, i) => h("th", { class: (opciones.num || []).includes(i) ? "num" : "" }, c)))),
    h("tbody", {}, filas.map((f) => h("tr", opciones.click ? { class: "click", onclick: () => opciones.click(f) } : {},
      f.celdas.map((c, i) => h("td", { class: (opciones.num || []).includes(i) ? "num" : "" }, c))))));
  return h("div", { class: "scroll" }, t);
}
function barra(valor, ia) {
  return h("div", { class: "bar" + (ia ? " ia" : "") }, h("i", { style: "width:" + Math.max(0, Math.min(1, valor)) * 100 + "%" }));
}

/* ------------------------------------------------------------------ CORPUS */
async function paginaCorpus() {
  try {
    const [salud, docs, calidad] = await Promise.all([api("/health"), api("/api/corpus"), api("/api/corpus/calidad")]);
    $("#m-articulos").textContent = salud.articulos;
    $("#m-vocab").textContent = salud.terminos_vocabulario;
    $("#m-modelos").textContent = salud.modelos_embeddings.length ? salud.modelos_embeddings.join(", ") : "ninguno";
    $("#m-ok").textContent = calidad.ok + " / " + calidad.total_extraidos;
    const cuerpo = $("#tabla-corpus"); vaciar(cuerpo);
    cuerpo.append(tabla(["ID", "Titulo", "Autores", "Palabras"],
      docs.map((d) => ({ id: d.id, celdas: ["#" + d.id, d.titulo, d.autores.join(", "), d.palabras] })),
      { num: [3], click: (f) => verDoc(f.id) }));
    const q = $("#tabla-calidad"); vaciar(q);
    q.append(tabla(["ID", "Palabras", "Caracteres", "Concordancia vs Java", "Estado", "Notas"],
      calidad.detalle.map((r) => ({ celdas: ["#" + r.id, r.palabras, r.caracteres, r.concordancia_java === null ? "n/a" : fmt(r.concordancia_java, 2),
        h("span", { class: "tag " + (r.estado === "OK" ? "ok" : "warn") }, r.estado),
        (r.problemas || []).join("; ") || (r.correccion_manual || "-")] })), { num: [1, 2, 3] }));
    estado("#estado", "");
  } catch (e) { estado("#estado", e.message, "error"); }
}
async function verDoc(id) {
  try {
    const d = await api("/api/corpus/" + id);
    const c = vaciar($("#detalle-doc"));
    const p = d.preprocesamiento;
    c.append(h("h2", {}, "#" + d.id + " - " + d.titulo), h("p", { class: "muted" }, d.autores.join(", ")),
      h("h3", {}, "Abstract (texto original extraido)"), h("div", { class: "abstract" }, d.abstract),
      h("h3", {}, "Preprocesamiento paso a paso"),
      pasos([["1. minusculas", p.minusculas], ["2. sin signos (solo letras)", p.sin_signos.replace(/ +/g, " ")],
        ["3. tokens (" + p.tokens.length + ")", p.tokens.join(" ")],
        ["4. sin stopwords (" + p.tokens_sin_stopwords.length + ")", p.tokens_sin_stopwords.join(" ")],
        ["5. con stemming (" + p.tokens_finales.length + ")", p.tokens_finales.join(" ")]]));
    c.scrollIntoView({ behavior: "smooth" });
  } catch (e) { estado("#estado", e.message, "error"); }
}
function pasos(lista) {
  return h("div", {}, lista.map(([t, v]) => h("details", {}, h("summary", {}, t), h("div", { class: "frag" }, v))));
}
function iniciarPreprocesar() {
  $("#btn-prep").addEventListener("click", async () => {
    try {
      const r = await api("/api/preprocesar", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: $("#texto-prep").value, stemming: $("#chk-stem").checked }) });
      vaciar($("#salida-prep")).append(pasos([["minusculas", r.minusculas], ["sin tildes", r.sin_tildes],
        ["sin signos", r.sin_signos.replace(/ +/g, " ")], ["tokens", r.tokens.join(" | ")],
        ["sin stopwords", r.tokens_sin_stopwords.join(" | ")], ["tokens finales", r.tokens_finales.join(" | ")]]));
      estado("#estado-prep", "");
    } catch (e) { estado("#estado-prep", e.message, "error"); }
  });
}

/* ------------------------------------------------------------------ SIMILITUD */
let _seleccion = [];
async function paginaSimilitud() {
  try {
    const docs = await api("/api/corpus");
    const lista = $("#lista-articulos");
    docs.forEach((d) => lista.append(h("label", { class: "chk" },
      h("input", { type: "checkbox", value: d.id, onchange: actualizarSeleccion }), h("span", {}, h("b", {}, "#" + d.id + " "), d.titulo))));
    $("#btn-comparar").addEventListener("click", comparar);
    actualizarSeleccion();
  } catch (e) { estado("#estado", e.message, "error"); }
}
function actualizarSeleccion() {
  _seleccion = [...document.querySelectorAll("#lista-articulos input:checked")].map((i) => Number(i.value));
  $("#contador").textContent = _seleccion.length + " seleccionados (minimo 2, maximo 6)";
  $("#btn-comparar").disabled = _seleccion.length < 2 || _seleccion.length > 6;
}
async function comparar() {
  estado("#estado", "Calculando (Levenshtein y Needleman-Wunsch recorren matrices de ~800x1000 celdas)...");
  $("#btn-comparar").disabled = true;
  try {
    const r = await api("/api/similarity", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ids: _seleccion }) });
    renderComparacion(r);
    estado("#estado", "Listo.", "ok");
  } catch (e) { estado("#estado", e.message, "error"); }
  actualizarSeleccion();
}
function renderComparacion(r) {
  const cont = vaciar($("#resultado"));
  r.pares.forEach((p) => {
    const filas = r.algoritmos.filter((a) => p.resultados[a.clave]).map((a) => {
      const x = p.resultados[a.clave]; const ia = a.tipo === "ia";
      let extra = "";
      if (a.clave === "levenshtein") extra = "distancia = " + x.distancia;
      if (a.clave === "needleman-wunsch") extra = "puntaje = " + x.puntaje;
      if (a.clave === "tfidf-coseno") extra = "angulo = " + fmt(x.angulo_grados, 1) + " grados";
      if (a.clave === "jaccard") extra = x.interseccion + " en comun / " + x.union + " en la union";
      if (ia) extra = "euclidiana d=" + fmt(x.distancia_euclidiana, 3) + " -> sim " + fmt(x.similitud_euclidiana, 3);
      return { celdas: [a.nombre, h("span", { class: "tag " + (ia ? "ia" : "ok") }, ia ? "IA" : "clasico"),
        h("b", {}, fmt(x.similitud)), barra(x.similitud, ia), extra, ms(x.ms)] };
    });
    cont.append(h("div", { class: "panel" },
      h("h2", {}, "#" + p.a + " vs #" + p.b),
      h("p", { class: "muted" }, r.titulos[p.a] + "  <->  " + r.titulos[p.b]),
      tabla(["Algoritmo", "Tipo", "Similitud [0,1]", "", "Detalle", "Tiempo"], filas, { num: [2] }),
      h("div", { class: "row", style: "margin-top:10px" }, h("button", { class: "secondary", onclick: () => verDetalle(p.a, p.b) }, "Ver calculo detallado (TF-IDF y Jaccard)")),
      h("div", { id: "detalle-" + p.a + "-" + p.b })));
  });
  const sel = h("select", { onchange: () => cambiarMapa(r.ids) }, r.algoritmos.map((a) => h("option", { value: a.clave }, a.nombre)));
  sel.id = "sel-mapa";
  cont.append(h("div", { class: "panel" }, h("h2", {}, "Matriz de similitud"), h("div", { class: "row" }, h("div", { class: "grow" }, sel)),
    h("p", {}, h("img", { id: "img-mapa", class: "plot", alt: "Mapa de calor de similitud" }))));
  cambiarMapa(r.ids);
  cont.append(h("div", { class: "panel conclusion" }, h("b", {}, "Como leer esto: "),
    "Levenshtein y Needleman-Wunsch comparan secuencias de caracteres (forma); Coseno-TF-IDF y Jaccard comparan vocabulario (palabras compartidas); " +
    "los embeddings comparan significado aproximado (palabras vecinas en el espacio vectorial). Por eso los valores no son comparables entre si en magnitud: " +
    "compare el orden de los pares, no el numero absoluto."));
}
function cambiarMapa(ids) {
  $("#img-mapa").src = "/plot/similarity.png?ids=" + ids.join(",") + "&algoritmo=" + encodeURIComponent($("#sel-mapa").value);
}
async function verDetalle(a, b) {
  const dest = $("#detalle-" + a + "-" + b);
  try {
    const d = await api("/api/similarity/detalle?a=" + a + "&b=" + b);
    vaciar(dest).append(h("h3", {}, "Coseno TF-IDF"),
      h("p", {}, "producto punto = ", fmt(d.tfidf.producto_punto, 6), " | |A| = ", fmt(d.tfidf.norma_a, 6), " | |B| = ", fmt(d.tfidf.norma_b, 6),
        " | coseno = ", fmt(d.tfidf.coseno, 6), " | angulo = ", fmt(d.tfidf.angulo_grados, 2), " grados"),
      h("p", { class: "muted" }, "Terminos distintos (union): " + d.tfidf.terminos_union + " de un vocabulario de " + d.tfidf.tamano_vocabulario + ". Se muestran los de mayor aporte al producto punto."),
      tabla(["Termino (stem)", "df", "idf", "TF A", "TF B", "w A", "w B", "w A x w B"],
        d.tfidf.terminos_mayor_aporte.slice(0, 15).map((f) => ({ celdas: [f.termino, f.df, fmt(f.idf, 3), fmt(f.tf_a, 4), fmt(f.tf_b, 4), fmt(f.w_a, 4), fmt(f.w_b, 4), fmt(f.producto, 5)] })), { num: [1, 2, 3, 4, 5, 6, 7] }),
      h("h3", {}, "Jaccard"),
      h("p", {}, "|A| = " + d.jaccard.tamano_a + ", |B| = " + d.jaccard.tamano_b + ", |A inter B| = " + d.jaccard.interseccion.length + ", |A union B| = " + d.jaccard.tamano_union + " -> J = " + fmt(d.jaccard.similitud, 4)),
      h("div", { class: "chips" }, d.jaccard.interseccion.map((t) => h("span", { class: "chip" }, t))));
  } catch (e) { vaciar(dest).append(h("div", { class: "status error" }, e.message)); }
}

/* ------------------------------------------------------------------ CLUSTERING */
let _cl = null, _crit = "average";
async function paginaClustering() {
  try {
    _cl = await api("/api/clustering/comparar");
    const mejor = _cl.criterios.find((c) => c.criterio === _cl.mejor);
    $("#tabla-metricas").append(tabla(["Criterio", "Correlacion cofenetica (CCC)", "Mejor k (silueta)", "Silueta en ese k", "Ranking"],
      _cl.criterios.map((c) => ({ celdas: [h("b", {}, c.nombre), fmt(c.ccc, 4), c.mejor_k, fmt(c.mejor_silueta, 4),
        h("span", { class: "tag " + (c.criterio === _cl.mejor ? "ok" : "warn") }, "#" + (_cl.ranking.indexOf(c.criterio) + 1))] })), { num: [1, 2, 3] }));
    $("#conclusion").textContent = "Conclusion: " + mejor.nombre + " es el criterio mas coherente (mayor correlacion cofenetica = " + fmt(mejor.ccc, 4) +
      "): su arbol conserva mejor las distancias originales entre abstracts. La silueta es baja en los tres criterios (abstracts cortos y vocabulario compartido), " +
      "por lo que no hay grupos nitidamente separados; se usa solo como criterio de apoyo.";
    $("#img-metricas").src = "/plot/clustering_metricas.png";
    const tabs = $("#tabs-crit");
    _cl.criterios.forEach((c) => tabs.append(h("button", { "data-c": c.criterio, class: c.criterio === _crit ? "on" : "", onclick: () => elegirCriterio(c.criterio) }, c.nombre)));
    $("#rng-k").addEventListener("change", () => dibujar());
    dibujar();
    estado("#estado", "");
  } catch (e) { estado("#estado", e.message, "error"); }
}
function elegirCriterio(c) {
  _crit = c;
  document.querySelectorAll("#tabs-crit button").forEach((b) => b.classList.toggle("on", b.dataset.c === c));
  dibujar();
}
async function dibujar() {
  const k = $("#rng-k").value; $("#lbl-k").textContent = k;
  $("#img-dendro").src = "/plot/dendrogram.png?criterio=" + _crit + "&k=" + k;
  const c = _cl.criterios.find((x) => x.criterio === _crit);
  vaciar($("#historial")).append(tabla(["Paso", "Une cluster A", "con cluster B", "Distancia", "Tamano"],
    c.historial.map((f, i) => ({ celdas: [i + 1, nombreCluster(f.a), nombreCluster(f.b), fmt(f.distancia, 4), f.tamano] })), { num: [0, 3, 4] }));
  try {
    const g = await api("/api/clustering/grupos?criterio=" + _crit + "&k=" + k);
    vaciar($("#grupos")).append(h("p", { class: "muted" }, "Silueta con k = " + k + ": " + fmt(g.silueta, 4)),
      ...g.grupos.map((gr, i) => h("details", { open: "" }, h("summary", {}, "Grupo " + (i + 1) + " (" + gr.length + " articulos)"),
        h("ul", {}, gr.map((d) => h("li", {}, "#" + d.id + " " + d.titulo))))));
  } catch (e) { vaciar($("#grupos")).append(h("div", { class: "status error" }, e.message)); }
}
const nombreCluster = (id) => (id < 20 ? "documento #" + _cl.documentos[id].id : "cluster " + id);

/* ------------------------------------------------------------------ PATRONES */
async function buscar() {
  const patron = $("#patron").value;
  const alg = $("#alg").value;
  const q = "patron=" + encodeURIComponent(patron) + "&algoritmo=" + alg + "&distinguir_mayusculas=" + ($("#may").checked ? 1 : 0);
  estado("#estado", "Buscando...");
  try {
    const r = await api("/api/patterns/search?" + q);
    const cont = vaciar($("#resultado"));
    cont.append(h("div", { class: "panel" }, h("div", { class: "metrics" },
      m("Ocurrencias", r.total), m("Articulos con coincidencias", r.documentos_con_coincidencias + " / 20"),
      m("Preprocesamiento", ms(r.ms_preprocesamiento)), m("Busqueda", ms(r.ms_busqueda)))));
    if (r.comparacion) {
      cont.append(h("div", { class: "panel" }, h("h2", {}, "Los tres algoritmos"),
        h("p", {}, r.comparacion.coinciden ? h("span", { class: "tag ok" }, "Los tres devuelven exactamente las mismas posiciones") : h("span", { class: "tag bad" }, "ATENCION: difieren")),
        tabla(["Algoritmo", "Ocurrencias", "Preprocesamiento", "Busqueda", "Comparaciones", "Colisiones"],
          Object.keys(r.comparacion.algoritmos).map((a) => { const x = r.comparacion.algoritmos[a];
            return { celdas: [a, x.total, ms(x.ms_preprocesamiento), ms(x.ms_busqueda), x.comparaciones, a === "rabin-karp" ? x.colisiones : "-"] }; }), { num: [1, 2, 3, 4, 5] })));
    }
    if (r.total === 0) cont.append(h("div", { class: "status" }, "Sin coincidencias para \"" + patron + "\"."));
    r.resultados.forEach((d) => cont.append(h("div", { class: "panel" },
      h("h3", {}, "#" + d.id + " - " + d.titulo + " (" + d.cantidad + ")"),
      d.ocurrencias.map((o) => h("div", { class: "frag" }, o.recortado_inicio ? "..." : "", o.antes, h("mark", {}, o.coincidencia), o.despues, o.recortado_fin ? "..." : "",
        h("span", { class: "muted" }, "   [posicion " + o.posicion + "]"))),
      h("div", { class: "row" }, ["kmp", "boyer-moore", "rabin-karp"].map((a) =>
        h("button", { class: "secondary", onclick: (ev) => verIteraciones(ev.target.closest(".panel"), d.id, patron, a) }, "Iteraciones " + a))),
      h("div", { class: "traza" }))));
    estado("#estado", "Listo.", "ok");
  } catch (e) { estado("#estado", e.message, "error"); }
}
const m = (t, v) => h("div", { class: "metric" }, h("span", {}, t), h("strong", {}, v));
function verIteraciones(panel, id, patron, alg) {
  const dest = vaciar(panel.querySelector(".traza"));
  dest.append(h("img", { class: "plot", alt: "Iteraciones y desplazamientos", src: "/plot/patterns.png?patron=" + encodeURIComponent(patron) + "&doc=" + id + "&algoritmo=" + alg + "&distinguir_mayusculas=" + ($("#may").checked ? 1 : 0) }));
}
async function benchmark() {
  const patron = $("#patron").value;
  estado("#estado-bench", "Midiendo (puede tardar unos segundos)...");
  try {
    const r = await api("/api/patterns/benchmark?patron=" + encodeURIComponent(patron) + "&repeticiones=5");
    const dest = vaciar($("#bench"));
    const filaAlg = (x) => Object.keys(x).map((a) => ({ celdas: [a, ms(x[a].ms_preprocesamiento), ms(x[a].ms_busqueda), x[a].comparaciones, x[a].ocurrencias] }));
    dest.append(h("h3", {}, "Corpus completo (n = " + r.n + " caracteres, m = " + r.m + ", mediana de " + r.repeticiones + " corridas)"),
      tabla(["Algoritmo", "Preprocesamiento", "Busqueda", "Comparaciones", "Ocurrencias"], filaAlg(r.corpus), { num: [1, 2, 3, 4] }),
      h("h3", {}, "Escalabilidad (el corpus repetido k veces)"),
      tabla(["k", "n", "KMP busqueda", "Boyer-Moore busqueda", "Rabin-Karp busqueda"], r.escalabilidad.map((f) => ({ celdas: [f.factor, f.n,
        ms(f.algoritmos["kmp"].ms_busqueda), ms(f.algoritmos["boyer-moore"].ms_busqueda), ms(f.algoritmos["rabin-karp"].ms_busqueda)] })), { num: [0, 1, 2, 3, 4] }),
      h("h3", {}, "Casos limite sinteticos (n = " + r.sinteticos[0].n + ", m = " + r.sinteticos[0].m + ")"),
      tabla(["Caso", "KMP", "Boyer-Moore", "Rabin-Karp"], r.sinteticos.map((f) => ({ celdas: [f.caso,
        ms(f.algoritmos["kmp"].ms_busqueda) + " (" + f.algoritmos["kmp"].comparaciones + " comp.)",
        ms(f.algoritmos["boyer-moore"].ms_busqueda) + " (" + f.algoritmos["boyer-moore"].comparaciones + " comp.)",
        ms(f.algoritmos["rabin-karp"].ms_busqueda) + " (" + f.algoritmos["rabin-karp"].comparaciones + " comp.)"] }))));
    estado("#estado-bench", "");
  } catch (e) { estado("#estado-bench", e.message, "error"); }
}
function paginaPatrones() {
  $("#btn-buscar").addEventListener("click", buscar);
  $("#patron").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar(); });
  $("#btn-bench").addEventListener("click", benchmark);
}

/* ------------------------------------------------------------------ DOCUMENTACION */
async function paginaDocs() {
  try {
    const docs = await api("/api/algorithm-docs");
    $("#tabla-algoritmos").append(tabla(["Req.", "Algoritmo", "Idea", "Tiempo", "Espacio", "Archivo"],
      docs.map((d) => ({ celdas: [d.requerimiento, h("b", {}, d.nombre), d.idea, h("span", { class: "mono" }, d.tiempo), h("span", { class: "mono" }, d.espacio), h("span", { class: "mono" }, d.archivo)] }))));
  } catch (e) { estado("#estado", e.message, "error"); }
}

document.addEventListener("DOMContentLoaded", () => {
  const pagina = document.body.dataset.page;
  const activa = document.querySelector('.nav a[data-m="' + pagina + '"]'); if (activa) activa.classList.add("active");
  ({ corpus: () => { paginaCorpus(); iniciarPreprocesar(); }, similarity: paginaSimilitud, clustering: paginaClustering,
     patterns: paginaPatrones, docs: paginaDocs }[pagina] || (() => {}))();
});
