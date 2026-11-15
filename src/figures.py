"""Gera as visualizações do artigo.

Saídas (a partir de data/processed):
  docs/assets/charts.js      figuras interativas Plotly (JSON embutido; funciona até via file://)
  docs/assets/fig*.png       versões estáticas (matplotlib) para README / fallback sem JS

Uso:  python -m src.figures
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"

# Paleta do artigo (papel quente + azul-tinta, verde-petróleo e laranja queimado)
INK, MUTED, GRID = "#1c2a3a", "#6b7280", "#e5dfd3"
BLUE, TEAL, RUST, SAND = "#1f3a5f", "#2a7f78", "#c2501c", "#b9ad94"
PERIODO_COR = [BLUE, TEAL, RUST]
EVENTOS = [  # (x, rótulo) — marcos contextuais, NÃO causais
    (2008.9, "1ª UPP<br>(dez/2008)"),
    (2018.0, "Intervenção<br>federal (2018)"),
    (2020.45, "ADPF 635<br>(jun/2020)"),
]

BASE = dict(
    font=dict(family="Inter, system-ui, sans-serif", size=13, color=INK),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=56, r=20, t=24, b=48),
    hoverlabel=dict(font_family="Inter, system-ui, sans-serif"),
    legend=dict(orientation="h", y=-0.18, x=0),
)
AX = dict(gridcolor=GRID, zeroline=False, linecolor=GRID, ticks="outside", tickcolor=GRID)


def carregar() -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(ROOT / "data" / "processed" / "vitimas_auto_resistencia.csv.gz")
    resumo = json.loads((ROOT / "data" / "processed" / "resumo_estatistico.json").read_text(encoding="utf-8"))
    return df, resumo


# --------------------------------------------------------------------------- #
# Plotly
# --------------------------------------------------------------------------- #
def fig_serie(df, resumo) -> go.Figure:
    f = go.Figure()
    for p, cor in zip(resumo["periodos"], PERIODO_COR):
        f.add_vrect(x0=p["ano_ini"] - 0.5, x1=p["ano_fim"] + 0.5, fillcolor=cor, opacity=0.07, line_width=0)
        f.add_annotation(
            x=(p["ano_ini"] + p["ano_fim"]) / 2, y=1.0, yref="paper", yanchor="bottom",
            text=f"<b>média {p['media']:.0f}</b>", showarrow=False, font=dict(size=12, color=cor),
        )
        f.add_shape(
            type="line", x0=p["ano_ini"] - 0.5, x1=p["ano_fim"] + 0.5, y0=p["media"], y1=p["media"],
            line=dict(color=cor, width=1.5, dash="dot"),
        )
    f.add_trace(go.Scatter(
        x=df.ano.tolist(), y=df.total_jan_abr.tolist(), mode="lines+markers", name="Vítimas (jan–abr)",
        line=dict(color=INK, width=2.5), marker=dict(size=7, color=INK),
        hovertemplate="<b>%{x}</b><br>%{y} vítimas<extra></extra>",
    ))
    f.add_trace(go.Scatter(
        x=df.ano.tolist(), y=df.media_movel_3a.tolist(), mode="lines", name="Média móvel de 3 anos",
        line=dict(color=SAND, width=3), hovertemplate="<b>%{x}</b><br>média móvel %{y:.0f}<extra></extra>",
    ))
    for (x, txt), y in zip(EVENTOS, (0.02, 0.02, 0.17)):
        f.add_vline(x=x, line=dict(color=MUTED, width=1, dash="dash"))
        f.add_annotation(x=x, y=y, yref="paper", text=txt, showarrow=False, xanchor="left", xshift=4,
                         font=dict(size=11, color=MUTED), align="left")
    f.update_layout(**{**BASE, "margin": dict(l=56, r=20, t=40, b=60)}, yaxis=dict(title="Vítimas no 1º quadrimestre", rangemode="tozero", **AX),
                    xaxis=dict(dtick=2, **AX), hovermode="x unified")
    return f


def fig_variacao(df, resumo) -> go.Figure:
    d = df.dropna(subset=["diferenca_pct"])
    cores = [RUST if v > 0 else TEAL if v < 0 else SAND for v in d.diferenca_pct]
    f = go.Figure(go.Bar(
        x=d.ano.tolist(), y=d.diferenca_pct.round(1).tolist(), marker_color=cores,
        customdata=d[["diferenca_absoluta", "total_jan_abr"]].values.tolist(),
        hovertemplate="<b>%{x}</b><br>%{y:+.1f}% vs. ano anterior<br>%{customdata[0]:+d} vítimas (total %{customdata[1]})<extra></extra>",
    ))
    f.update_layout(**BASE, showlegend=False, bargap=0.25,
                    yaxis=dict(title="Variação % sobre o ano anterior", ticksuffix="%", **AX),
                    xaxis=dict(dtick=1, tickangle=-45, **AX))
    return f


def fig_indice(df, resumo) -> go.Figure:
    base_pop = df.populacao.iloc[0]
    f = go.Figure()
    series = [
        ("Vítimas (nº absoluto)", df.indice_2003, INK, "solid", 3),
        ("Taxa por 100 mil hab.", df.taxa_100k / df.taxa_100k.iloc[0] * 100, RUST, "solid", 3),
        ("População do município", df.populacao / base_pop * 100, SAND, "solid", 3),
    ]
    for nome, y, cor, dash, w in series:
        f.add_trace(go.Scatter(x=df.ano.tolist(), y=y.round(1).tolist(), name=nome, mode="lines+markers",
                               line=dict(color=cor, width=w, dash=dash), marker=dict(size=5),
                               hovertemplate=f"{nome}: " + "%{y:.0f}<extra></extra>"))
    f.add_hline(y=100, line=dict(color=MUTED, width=1, dash="dot"))
    f.update_layout(**BASE, hovermode="x unified", yaxis=dict(title="Índice (2003 = 100)", rangemode="tozero", **AX),
                    xaxis=dict(dtick=2, **AX))
    return f


def fig_periodos(df, resumo) -> go.Figure:
    f = go.Figure()
    for (nome, g), cor in zip(df.groupby("periodo"), PERIODO_COR):
        f.add_trace(go.Box(
            y=g.total_jan_abr.tolist(), name=nome.split(" ")[1].strip("()"), boxpoints="all", jitter=0.5, pointpos=0,
            marker=dict(color=cor, size=8), line=dict(color=cor), fillcolor="rgba(0,0,0,0)", boxmean=True,
            text=g.ano.astype(str).tolist(), hovertemplate="<b>%{text}</b>: %{y} vítimas<extra></extra>",
        ))
    f.update_layout(**BASE, showlegend=False, yaxis=dict(title="Vítimas no 1º quadrimestre", rangemode="tozero", **AX),
                    xaxis=dict(title="Patamar (segmentação em 3 períodos)", **AX))
    return f


# --------------------------------------------------------------------------- #
# Matplotlib (estático)
# --------------------------------------------------------------------------- #
def _estilo(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED)


def estaticas(df, resumo) -> None:
    plt.rcParams.update({"font.size": 11, "text.color": INK, "axes.labelcolor": INK, "figure.facecolor": "white"})

    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=160)
    for p, cor in zip(resumo["periodos"], PERIODO_COR):
        ax.axvspan(p["ano_ini"] - .5, p["ano_fim"] + .5, color=cor, alpha=.07, lw=0)
        ax.hlines(p["media"], p["ano_ini"] - .5, p["ano_fim"] + .5, color=cor, ls=":", lw=1.6)
        ax.text((p["ano_ini"] + p["ano_fim"]) / 2, 352, f"média {p['media']:.0f}", ha="center", color=cor, weight="bold")
    ax.plot(df.ano, df.media_movel_3a, color=SAND, lw=3, label="Média móvel de 3 anos")
    ax.plot(df.ano, df.total_jan_abr, color=INK, lw=2.4, marker="o", label="Vítimas (jan–abr)")
    ax.set_ylim(0, 370); ax.set_xticks(range(2003, 2023, 2)); ax.set_ylabel("Vítimas no 1º quadrimestre")
    ax.legend(frameon=False, loc="lower left", ncols=2); _estilo(ax)
    fig.tight_layout(); fig.savefig(ASSETS / "fig1_serie_temporal.png"); plt.close(fig)

    d = df.dropna(subset=["diferenca_pct"])
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=160)
    ax.bar(d.ano, d.diferenca_pct, color=[RUST if v > 0 else TEAL for v in d.diferenca_pct])
    ax.axhline(0, color=MUTED, lw=.8); ax.set_xticks(d.ano); ax.tick_params(axis="x", rotation=60)
    ax.set_ylabel("Variação % sobre o ano anterior"); _estilo(ax)
    fig.tight_layout(); fig.savefig(ASSETS / "fig2_variacao_anual.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.4), dpi=160)
    ax.plot(df.ano, df.indice_2003, color=INK, lw=2.6, label="Vítimas (nº absoluto)")
    ax.plot(df.ano, df.taxa_100k / df.taxa_100k.iloc[0] * 100, color=RUST, lw=2.6, label="Taxa por 100 mil hab.")
    ax.plot(df.ano, df.populacao / df.populacao.iloc[0] * 100, color=SAND, lw=2.6, label="População")
    ax.axhline(100, color=MUTED, ls=":", lw=1); ax.set_ylim(0, 125); ax.set_xticks(range(2003, 2023, 2))
    ax.set_ylabel("Índice (2003 = 100)"); ax.legend(frameon=False, ncols=3, loc="lower left"); _estilo(ax)
    fig.tight_layout(); fig.savefig(ASSETS / "fig3_indice_2003.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.4), dpi=160)
    grupos = [g.total_jan_abr.to_numpy() for _, g in df.groupby("periodo")]
    rotulos = [p["rotulo"] for p in resumo["periodos"]]
    bp = ax.boxplot(grupos, tick_labels=rotulos, widths=.45, showmeans=True, patch_artist=True)
    for patch, cor in zip(bp["boxes"], PERIODO_COR):
        patch.set(facecolor="none", edgecolor=cor, lw=1.8)
    for g, cor, i in zip(grupos, PERIODO_COR, range(1, 4)):
        ax.scatter([i] * len(g), g, color=cor, zorder=3, s=26)
    ax.set_ylim(0, 360); ax.set_ylabel("Vítimas no 1º quadrimestre"); _estilo(ax)
    fig.tight_layout(); fig.savefig(ASSETS / "fig4_periodos.png"); plt.close(fig)


def main() -> None:
    df, resumo = carregar()
    ASSETS.mkdir(parents=True, exist_ok=True)
    figs = {"serie": fig_serie(df, resumo), "variacao": fig_variacao(df, resumo),
            "indice": fig_indice(df, resumo), "periodos": fig_periodos(df, resumo)}
    payload = {k: json.loads(v.to_json()) for k, v in figs.items()}
    tabela = df[["ano", "total_jan_abr", "diferenca_absoluta", "diferenca_pct", "populacao", "taxa_100k", "media_mensal", "periodo"]]
    (ASSETS / "charts.js").write_text(
        "// Gerado por src/figures.py — não editar à mão.\nwindow.FIGS = " + json.dumps(payload, ensure_ascii=False)
        + ";\nwindow.DADOS = " + tabela.to_json(orient="records", force_ascii=False) + ";\n",
        encoding="utf-8",
    )
    estaticas(df, resumo)
    print("ok:", sorted(p.name for p in ASSETS.glob("*") if p.is_file()))


if __name__ == "__main__":
    main()
