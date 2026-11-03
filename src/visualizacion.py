"""Graficas PNG con matplotlib. Los dendrogramas se dibujan a partir de MI historial de fusiones (no scipy)."""
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from src.clustering import NOMBRES, coordenadas_dendrograma, cortar_en_k  # noqa: E402

PALETA = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2", "#be185d", "#4d7c0f"]


def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def png_dendrograma(historial, n, etiquetas, criterio, ccc=None, k=None):
    orden, segmentos = coordenadas_dendrograma(historial, n)
    fig, ax = plt.subplots(figsize=(10, 5.2))
    for (x1, y1, x2, y2) in segmentos:
        ax.plot([x1, x2], [y1, y2], color="#334155", linewidth=1.4, solid_capstyle="round")
    if k is not None and 2 <= k <= n:
        h = historial
        altura = (h[n - k - 1]["distancia"] + h[n - k]["distancia"]) / 2.0
        ax.axhline(altura, color="#dc2626", linestyle="--", linewidth=1)
        ax.text(n - 0.5, altura, " corte k=%d" % k, color="#dc2626", va="bottom", ha="right", fontsize=9)
        grupos = cortar_en_k(historial, n, k)
    else:
        grupos = None
    ax.set_xticks(range(n))
    ax.set_xticklabels([etiquetas[d] for d in orden], rotation=90, fontsize=9)
    if grupos is not None:
        for lab, d in zip(ax.get_xticklabels(), orden):
            lab.set_color(PALETA[grupos[d] % len(PALETA)])
            lab.set_fontweight("bold")
    ax.set_ylabel("Distancia (1 - coseno TF-IDF)")
    titulo = NOMBRES.get(criterio, criterio)
    if ccc is not None:
        titulo += "  |  correlacion cofenetica = %.4f" % ccc
    ax.set_title(titulo, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(-0.6, n - 0.4)
    return _png(fig)


def png_metricas_clustering(resultados):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8))
    nombres = [r["criterio"].capitalize() for r in resultados]
    colores = PALETA[:len(resultados)]
    a1.bar(nombres, [r["ccc"] for r in resultados], color=colores)
    a1.set_title("Correlacion cofenetica (mayor = mejor)", fontsize=10)
    a1.set_ylim(0, 1)
    for i, r in enumerate(resultados):
        a1.text(i, r["ccc"] + 0.015, "%.3f" % r["ccc"], ha="center", fontsize=9)
    for i, r in enumerate(resultados):
        a2.plot([x["k"] for x in r["siluetas"]], [x["silueta"] for x in r["siluetas"]], marker="o",
                color=colores[i], label=r["criterio"].capitalize())
    a2.set_title("Silueta promedio segun k grupos", fontsize=10)
    a2.set_xlabel("k")
    a2.legend(fontsize=8)
    for a in (a1, a2):
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _png(fig)


def png_heatmap(matriz, etiquetas, titulo):
    n = len(matriz)
    fig, ax = plt.subplots(figsize=(max(4.5, n * 0.9), max(3.8, n * 0.8)))
    datos = [[(matriz[i][j] if matriz[i][j] is not None else 0.0) for j in range(n)] for i in range(n)]
    im = ax.imshow(datos, cmap="viridis", vmin=0, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(etiquetas, rotation=45, ha="right")
    ax.set_yticklabels(etiquetas)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, "%.2f" % datos[i][j], ha="center", va="center", fontsize=8,
                    color="white" if datos[i][j] < 0.6 else "black")
    ax.set_title(titulo, fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    return _png(fig)


def png_alineaciones(texto, patron, algoritmo, traza, max_filas=None):
    """Grafica de iteraciones y desplazamientos: una fila por alineamiento del patron sobre el texto."""
    m = len(patron)
    n = len(texto)
    filas = []
    if algoritmo == "kmp":
        grupos = []
        for ev in traza:
            if len(grupos) == 0 or grupos[-1]["s"] != ev["s"]:
                grupos.append({"s": ev["s"], "comparaciones": 0, "falla_en": None, "completo": False, "maximo": 0})
            g = grupos[-1]
            g["comparaciones"] += 1
            if ev["ok"]:
                g["maximo"] = ev["j"] + 1
                if ev["j"] == m - 1:
                    g["completo"] = True
            else:
                g["falla_en"] = ev["j"]
        for k, g in enumerate(grupos):
            sig = grupos[k + 1]["s"] if k + 1 < len(grupos) else None
            filas.append({"s": g["s"], "ancho": (g["maximo"] + (1 if g["falla_en"] is not None else 0)) or 1,
                          "ok": g["completo"], "texto": "%d comp." % g["comparaciones"],
                          "desp": (sig - g["s"]) if sig is not None else None})
    elif algoritmo == "boyer-moore":
        for k, ev in enumerate(traza):
            sig = traza[k + 1]["s"] if k + 1 < len(traza) else None
            filas.append({"s": ev["s"], "ancho": m, "ok": ev["j"] < 0,
                          "texto": ("OCURRENCIA" if ev["j"] < 0 else "falla j=%d, %s, +%d" % (ev["j"], ev["regla"], ev["desplazamiento"])),
                          "desp": ev["desplazamiento"], "resaltar_desde": ev["j"] if ev["j"] >= 0 else 0})
    else:  # rabin-karp
        for ev in traza:
            filas.append({"s": ev["s"], "ancho": m, "ok": ev["real"], "colision": ev["colision"],
                          "texto": "hash %d%s" % (ev["hash"], " = hash patron" if ev["igual"] else ""), "desp": 1})
    total = len(filas)
    if max_filas is None:
        max_filas = 60 if algoritmo == "rabin-karp" else 30
    filas = filas[:max_filas]
    alto = max(3.0, (0.22 if algoritmo == "rabin-karp" else 0.32) * len(filas) + 1.8)
    ancho_fig = max(9.0, min(22.0, n * 0.16))
    fig, ax = plt.subplots(figsize=(ancho_fig, alto))
    for i, ch in enumerate(texto):
        ax.text(i + 0.5, -0.9, ch if ch != " " else "\u00b7", ha="center", va="center", fontsize=7, family="monospace")
    for r, f in enumerate(filas):
        if f.get("ok"):
            color = "#16a34a"
        elif f.get("colision"):
            color = "#7c3aed"
        elif algoritmo == "rabin-karp":
            color = "#cbd5e1"
        else:
            color = "#f59e0b"
        ax.add_patch(Rectangle((f["s"], r), f["ancho"], 0.8, facecolor=color, edgecolor="#1e293b", alpha=0.85))
        for k in range(min(m, int(f["ancho"]))):
            if f["s"] + k < n:
                pass
        ax.text(f["s"] + f["ancho"] + 0.4, r + 0.4, f["texto"], va="center", fontsize=6.5)
        if f.get("desp"):
            ax.annotate("", xy=(f["s"] + f["desp"], r + 0.4), xytext=(f["s"], r + 0.4),
                        arrowprops=dict(arrowstyle="->", color="#0f172a", lw=0.8))
    ax.set_xlim(-1, n + 1)
    ax.set_ylim(len(filas), -1.6)
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels(["iter %d" % (i + 1) for i in range(len(filas))], fontsize=7)
    ax.set_xlabel("posicion en el texto")
    sub = "" if total <= max_filas else " (primeras %d de %d iteraciones)" % (max_filas, total)
    ax.set_title("%s: patron '%s' sobre el texto%s" % (
        {"kmp": "KMP", "boyer-moore": "Boyer-Moore", "rabin-karp": "Rabin-Karp"}[algoritmo], patron, sub), fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    return _png(fig)


def png_barras_tiempos(titulo, nombres, prep, busq, unidad="ms"):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    x = range(len(nombres))
    ax.bar([i - 0.2 for i in x], prep, width=0.4, label="Preprocesamiento", color="#2563eb")
    ax.bar([i + 0.2 for i in x], busq, width=0.4, label="Busqueda", color="#d97706")
    ax.set_xticks(list(x))
    ax.set_xticklabels(nombres)
    ax.set_ylabel("tiempo (%s)" % unidad)
    ax.set_title(titulo, fontsize=10)
    ax.legend(fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    return _png(fig)


def png_escalabilidad(titulo, tamanos, series):
    """series: dict nombre -> lista de tiempos (ms), una por tamano."""
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, nombre in enumerate(series):
        ax.plot(tamanos, series[nombre], marker="o", label=nombre, color=PALETA[i % len(PALETA)])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("tamano del texto n (caracteres)")
    ax.set_ylabel("tiempo de busqueda (ms)")
    ax.set_title(titulo, fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, which="both", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    return _png(fig)
