# Dicionário de dados

**Projeto:** Vítimas de auto de resistência no Município do Rio de Janeiro, 1º quadrimestre, 2003–2022
**Fonte:** Data.Rio — Tabela 2300 (dados do ISP-RJ; cálculos e tabulação do IPP). Consulta registrada na tabela: 24/05/2022.
**Granularidade:** 1 linha por ano (20 linhas). Cada valor refere-se ao acumulado de janeiro a abril.
**Arquivos:** `data/raw/tabela_2300_vitimas_auto_resistencia.xls` (original, intocado) → `data/processed/vitimas_auto_resistencia.csv.gz` e `.json` (via `python -m src.etl`).
**Codificação:** UTF-8 · separador `,` · decimal `.` · nulos = vazio (CSV) / `null` (JSON).

## Variáveis originais (herdadas da fonte)

| Variável | Significado | Tipo | Formato / unidade | Observações |
|---|---|---|---|---|
| `ano` | Ano de referência do 1º quadrimestre | `int` | `AAAA`, 2003–2022 | Chave única. Série contínua. |
| `total_jan_abr` | Vítimas de auto de resistência (homicídio decorrente de oposição à intervenção policial) registradas de jan. a abr. no MRJ | `int` | contagem de pessoas | Classificação policial provisória (ver nota da fonte). |
| `diferenca_absoluta` | `total_jan_abr` menos o valor do mesmo quadrimestre do ano anterior | `float` (inteiro com nulo) | vítimas | Nulo em 2003 (`..` na fonte = não se aplica). |
| `diferenca_pct` | Variação percentual sobre o ano anterior | `float` | % | Nulo em 2003. |
| `populacao` | População residente no município, projeção do ISP para o último mês do quadrimestre | `float` | habitantes | Valores fracionários por serem projeções. |
| `taxa_100k` | Vítimas por 100 mil habitantes = `total_jan_abr / populacao × 100000` | `float` | vítimas / 100 mil hab. | Taxa do quadrimestre, **não** anualizada. |
| `media_mensal` | `total_jan_abr / 4` | `float` | vítimas / mês | |

## Variáveis derivadas (criadas em `src/etl.py`)

| Variável | Significado | Tipo | Formato / unidade | Cálculo |
|---|---|---|---|---|
| `media_movel_3a` | Média móvel centrada de 3 anos | `float` | vítimas | `rolling(3, center=True).mean()`; nulo no 1º e no último ano. |
| `indice_2003` | Número-índice com base em 2003 | `float` | 2003 = 100 | `total / total[2003] × 100` |
| `z_score` | Desvio padronizado do total | `float` | desvios-padrão | `(x − média) / dp` (ddof = 1) |
| `outlier_iqr` | Outlier pelo critério de Tukey | `bool` | — | `x < Q1 − 1,5·IQR` ou `x > Q3 + 1,5·IQR` |
| `periodo` | Patamar da série (3 segmentos contíguos de menor soma de quadrados, mín. 3 anos) | `str` | `P1 (2003–2010)` … | Ver `best_segments()`. Descritivo, não inferencial. |

## Arquivos auxiliares gerados

| Arquivo | Conteúdo |
|---|---|
| `data/processed/resumo_estatistico.json` | Estatísticas descritivas, tendência (regressão linear, Kendall), correlação de Spearman, decomposição log da taxa e estatísticas por patamar. |
| `data/processed/etl_log.json` | Rastro do ETL: linhas lidas/descartadas, conversões de `..` para nulo, nulos por coluna e validação das métricas contra a fonte. |

## Notas e limitações

1. A classificação de um crime pela Polícia Civil é provisória e pode ser alterada no curso do inquérito, da denúncia ou da sentença (nota da fonte).
2. A tabela cobre apenas o 1º quadrimestre. Não representa totais anuais.
3. `..` na fonte significa "não se aplica dado numérico" e é convertido para nulo, sem imputação.
4. O valor de 2022 foi consultado em 24/05/2022 e pode ter sido revisado posteriormente.
