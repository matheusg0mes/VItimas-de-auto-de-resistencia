"""ETL e métricas — Vítimas de auto de resistência (MRJ, 1º quadrimestre, 2003-2022).

Pipeline determinístico: raw (.xls Data.Rio) -> processed (.csv.gz + .json).
Nenhuma operação é destrutiva: o bruto nunca é alterado e toda linha/valor
descartado ou convertido é registrado em ``data/processed/etl_log.json``.

Uso:
    python -m src.etl
"""
from __future__ import annotations

import itertools
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "tabela_2300_vitimas_auto_resistencia.xls"
PROCESSED = ROOT / "data" / "processed"
SHEET = "T 2300"

COLUNAS = {  # posição na planilha -> nome normalizado (snake_case)
    0: "ano",
    1: "total_jan_abr",
    2: "diferenca_absoluta",
    3: "diferenca_pct",
    4: "populacao",
    5: "taxa_100k",
    6: "media_mensal",
}


# --------------------------------------------------------------------------- #
# 1. Ingestão
# --------------------------------------------------------------------------- #
def load_raw(path: Path = RAW) -> pd.DataFrame:
    """Lê a aba principal sem cabeçalho (a planilha tem título e notas fora da grade)."""
    return pd.read_excel(path, sheet_name=SHEET, header=None)


# --------------------------------------------------------------------------- #
# 2. Limpeza
# --------------------------------------------------------------------------- #
def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Isola as linhas de dados (primeira coluna = ano com 4 dígitos) e tipa as colunas."""
    log: dict = {"linhas_brutas": int(len(raw))}

    eh_ano = raw[0].astype(str).str.fullmatch(r"\d{4}(\.0)?")
    dados = raw.loc[eh_ano, list(COLUNAS)].rename(columns=COLUNAS).copy()
    log["linhas_de_dados"] = int(len(dados))
    log["linhas_descartadas_titulo_notas_vazias"] = int((~eh_ano).sum())

    # '..' = "Não se aplica dado numérico" (nota da fonte) -> NaN explícito
    marcador = (dados.astype(str) == "..").sum()
    log["valores_'..'_convertidos_para_NaN"] = {k: int(v) for k, v in marcador.items() if v}
    dados = dados.replace("..", np.nan)

    dados["ano"] = dados["ano"].astype(float).astype(int)
    dados["total_jan_abr"] = pd.to_numeric(dados["total_jan_abr"]).astype("Int64")
    dados["diferenca_absoluta"] = pd.to_numeric(dados["diferenca_absoluta"]).astype("Int64")
    for c in ("diferenca_pct", "populacao", "taxa_100k", "media_mensal"):
        dados[c] = pd.to_numeric(dados[c]).astype(float)

    dados = dados.sort_values("ano").reset_index(drop=True)
    log["nulos_por_coluna"] = {k: int(v) for k, v in dados.isna().sum().items() if v}
    log["anos"] = [int(dados["ano"].min()), int(dados["ano"].max())]
    assert dados["ano"].is_unique, "anos duplicados"
    assert dados["ano"].diff().dropna().eq(1).all(), "série com buracos"
    return dados, log


# --------------------------------------------------------------------------- #
# 3. Validação das colunas derivadas da fonte
# --------------------------------------------------------------------------- #
def validate(df: pd.DataFrame) -> dict:
    """Recalcula as métricas que o IPP derivou e compara com o publicado."""
    total = df["total_jan_abr"].astype(float)
    checks = {
        "diferenca_absoluta": (total.diff(), df["diferenca_absoluta"].astype(float)),
        "diferenca_pct": (total.pct_change() * 100, df["diferenca_pct"]),
        "taxa_100k": (total / df["populacao"] * 1e5, df["taxa_100k"]),
        "media_mensal": (total / 4, df["media_mensal"]),
    }
    out = {}
    for nome, (calc, pub) in checks.items():
        m = calc.notna() & pub.notna()
        erro = float((calc[m] - pub[m]).abs().max())
        out[nome] = {"erro_abs_max": round(erro, 6), "consistente": bool(erro < 1e-3)}
    return out


# --------------------------------------------------------------------------- #
# 4. Métricas derivadas
# --------------------------------------------------------------------------- #
def best_segments(y: np.ndarray, k: int = 3, min_len: int = 3) -> list[tuple[int, int]]:
    """Segmentação em k patamares constantes (mínima soma de quadrados), força bruta.

    Retorna lista de (início, fim_exclusivo). Com n = 20 o custo é desprezível.
    """
    n = len(y)

    def sse(a: int, b: int) -> float:
        seg = y[a:b]
        return float(((seg - seg.mean()) ** 2).sum())

    melhor, cortes = np.inf, None
    for c in itertools.combinations(range(min_len, n - min_len + 1), k - 1):
        lims = (0, *c, n)
        if any(b - a < min_len for a, b in zip(lims, lims[1:])):
            continue
        custo = sum(sse(a, b) for a, b in zip(lims, lims[1:]))
        if custo < melhor:
            melhor, cortes = custo, lims
    return list(zip(cortes, cortes[1:]))


def add_metrics(df: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[int, int]]]:
    out = df.copy()
    total = out["total_jan_abr"].astype(float)

    out["media_movel_3a"] = total.rolling(3, center=True).mean().round(2)
    out["indice_2003"] = (total / total.iloc[0] * 100).round(1)
    out["z_score"] = ((total - total.mean()) / total.std(ddof=1)).round(3)
    q1, q3 = total.quantile([0.25, 0.75])
    iqr = q3 - q1
    out["outlier_iqr"] = (total < q1 - 1.5 * iqr) | (total > q3 + 1.5 * iqr)

    segs = best_segments(total.to_numpy())
    out["periodo"] = ""
    for i, (a, b) in enumerate(segs, 1):
        out.loc[a : b - 1, "periodo"] = f"P{i} ({out.ano[a]}–{out.ano[b - 1]})"
    return out, segs


def summary_stats(df: pd.DataFrame, segs: list[tuple[int, int]]) -> dict:
    total = df["total_jan_abr"].astype(float)
    taxa = df["taxa_100k"]
    anos = df["ano"].to_numpy()

    lin = stats.linregress(anos, total)
    tau, p_tau = stats.kendalltau(anos, total)
    rho_pop, p_pop = stats.spearmanr(df["populacao"], total)

    imax, imin = int(total.idxmax()), int(total.idxmin())
    periodos = []
    for a, b in segs:
        s = total.iloc[a:b]
        periodos.append(
            {
                "rotulo": f"{int(df.ano[a])}–{int(df.ano[b - 1])}",
                "ano_ini": int(df.ano[a]),
                "ano_fim": int(df.ano[b - 1]),
                "n": int(b - a),
                "media": round(float(s.mean()), 1),
                "desvio": round(float(s.std(ddof=1)), 1),
                "min": int(s.min()),
                "max": int(s.max()),
                "taxa_media": round(float(taxa.iloc[a:b].mean()), 2),
            }
        )

    return {
        "n_anos": int(len(df)),
        "total_acumulado": int(total.sum()),
        "media": round(float(total.mean()), 1),
        "mediana": float(total.median()),
        "desvio_padrao": round(float(total.std(ddof=1)), 1),
        "coef_variacao_pct": round(float(total.std(ddof=1) / total.mean() * 100), 1),
        "q1": float(total.quantile(0.25)),
        "q3": float(total.quantile(0.75)),
        "pico": {"ano": int(df.ano[imax]), "total": int(total[imax]), "taxa": round(float(taxa[imax]), 2)},
        "vale": {"ano": int(df.ano[imin]), "total": int(total[imin]), "taxa": round(float(taxa[imin]), 2)},
        "queda_pico_vale_pct": round(float((total[imin] / total[imax] - 1) * 100), 1),
        "var_2003_2022_pct": round(float((total.iloc[-1] / total.iloc[0] - 1) * 100), 1),
        "taxa_2003": round(float(taxa.iloc[0]), 2),
        "taxa_2022": round(float(taxa.iloc[-1]), 2),
        "populacao_var_pct": round(float((df.populacao.iloc[-1] / df.populacao.iloc[0] - 1) * 100), 1),
        # ln(taxa_f/taxa_i) = ln(total_f/total_i) - ln(pop_f/pop_i): quanto da queda da taxa vem do numerador
        "decomposicao_taxa": {
            "ln_taxa": round(float(np.log(taxa.iloc[-1] / taxa.iloc[0])), 3),
            "ln_total": round(float(np.log(total.iloc[-1] / total.iloc[0])), 3),
            "ln_populacao": round(float(-np.log(df.populacao.iloc[-1] / df.populacao.iloc[0])), 3),
            "parcela_numerador_pct": round(
                float(np.log(total.iloc[-1] / total.iloc[0]) / np.log(taxa.iloc[-1] / taxa.iloc[0]) * 100), 1
            ),
        },
        "tendencia_linear": {
            "inclinacao_por_ano": round(float(lin.slope), 2),
            "r2": round(float(lin.rvalue**2), 3),
            "p_valor": round(float(lin.pvalue), 3),
        },
        "kendall_tau": {"tau": round(float(tau), 3), "p_valor": round(float(p_tau), 3)},
        "spearman_total_vs_populacao": {"rho": round(float(rho_pop), 3), "p_valor": round(float(p_pop), 3)},
        "anos_com_alta": int((df["diferenca_absoluta"].dropna() > 0).sum()),
        "anos_com_queda": int((df["diferenca_absoluta"].dropna() < 0).sum()),
        "maior_alta_pct": {
            "ano": int(df.loc[df.diferenca_pct.idxmax(), "ano"]),
            "valor": round(float(df.diferenca_pct.max()), 1),
        },
        "maior_queda_pct": {
            "ano": int(df.loc[df.diferenca_pct.idxmin(), "ano"]),
            "valor": round(float(df.diferenca_pct.min()), 1),
        },
        "outliers_iqr": [int(a) for a in df.loc[df.outlier_iqr, "ano"]],
        "periodos": periodos,
    }


# --------------------------------------------------------------------------- #
# 5. Persistência (formatos abertos)
# --------------------------------------------------------------------------- #
def save(df: pd.DataFrame, resumo: dict, log: dict) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "vitimas_auto_resistencia.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})  # mtime=0 => saída byte a byte determinística
    df.to_json(PROCESSED / "vitimas_auto_resistencia.json", orient="records", force_ascii=False, indent=2)
    (PROCESSED / "resumo_estatistico.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PROCESSED / "etl_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def run() -> tuple[pd.DataFrame, dict, dict]:
    raw = load_raw()
    df, log = clean(raw)
    log["validacao_vs_fonte"] = validate(df)
    df, segs = add_metrics(df)
    resumo = summary_stats(df, segs)
    save(df, resumo, log)
    return df, resumo, log


if __name__ == "__main__":
    df, resumo, log = run()
    print(json.dumps(log, ensure_ascii=False, indent=2))
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
