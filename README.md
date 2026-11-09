# Vitimas-de-auto-de-resistencia

# Autos de Resistência no Município do Rio de Janeiro (1º quadrimestre, 2003–2022)

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-data%20analysis-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-interactive%20charts-3F4F75?logo=plotly&logoColor=white)
![Licença Código](https://img.shields.io/badge/c%C3%B3digo-MIT-green)
![Licença Dados/Texto](https://img.shields.io/badge/dados%20e%20texto-CC--BY%204.0-lightgrey)
![FAIR](https://img.shields.io/badge/FAIR-compliant-blue)
[![GitHub Pages](https://img.shields.io/badge/artigo-GitHub%20Pages-222?logo=github)](https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/)

> **Projeto Final de Disciplina** — Linguagem de Programação (Análise e Visualização de Dados com Python)
> **Curso:** Bacharelado em Sistemas de Informação · **Período:** 6º · **Semestre:** 2026.2
> **Instituição:** `[NOME DA INSTITUIÇÃO]`
> **Autores:** `[Nome 1]`, `[Nome 2]`, `[Nome 3]`
> **Docente:** `[Nome do(a) professor(a)]`

---

## 📌 Resumo Executivo

Este projeto analisa a série histórica de **vítimas de autos de resistência** (mortes decorrentes de intervenção policial registradas sob essa classificação) no **Município do Rio de Janeiro**, considerando o **1º quadrimestre (janeiro a abril) de cada ano entre 2003 e 2022**.

A base original apresenta, para cada ano, o número absoluto de vítimas, a **diferença absoluta** e a **diferença percentual** em relação ao ano anterior, a **taxa por 100 mil habitantes** e a **média mensal**. Segundo a descrição da própria fonte, o 1º quadrimestre de 2022 registrou **queda de 44,3%** em relação ao mesmo período de 2021.

O pipeline em Python realiza a aquisição, a higienização e a normalização da tabela, recalcula e valida as métricas derivadas e produz visualizações estáticas e interativas, comunicadas em um **artigo acadêmico em HTML** publicado via GitHub Pages.

🔗 **Artigo publicado:** https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/

## 🔑 Palavras-chave

`autos de resistência` · `letalidade policial` · `segurança pública` · `Rio de Janeiro` · `séries temporais` · `dados abertos` · `FAIR`

---

## ❓ Perguntas de Pesquisa

- **RQ1.** Como evoluiu o número absoluto de vítimas de autos de resistência no 1º quadrimestre entre 2003 e 2022, e quais foram os anos de pico e de menor ocorrência?
- **RQ2.** Essa evolução se mantém ao ser normalizada pela população (taxa por 100 mil habitantes), ou o crescimento populacional altera a leitura da tendência?
- **RQ3.** Quais foram as maiores variações interanuais (absolutas e percentuais) e como elas se distribuem ao longo das duas décadas?

> ⚠️ *Perguntas sujeitas à aprovação do docente (Semana 1 do cronograma).*

---

## 🗃️ Fonte dos Dados

| Item | Descrição |
|---|---|
| **Título original** | Vítimas de auto de resistência, por diferença absoluta, diferença percentual, taxa por cem mil habitantes e média mensal, segundo o 1º quadrimestre de cada ano, no Município do Rio de Janeiro entre 2003 e 2022 |
| **Portal** | [Data.Rio](https://www.data.rio/) — portal de dados abertos da Prefeitura da Cidade do Rio de Janeiro |
| **Link perene** | https://www.data.rio/documents/98961641129c4ee1aacd2445f82ac0ce/about |
| **Cobertura temporal** | 2003–2022 (1º quadrimestre de cada ano) |
| **Cobertura geográfica** | Município do Rio de Janeiro |
| **Granularidade** | Anual (agregado do 1º quadrimestre) |
| **Data de acesso** | 09/11/2026 |
| **Órgão produtor / fonte primária** | `[CONFIRMAR NA PÁGINA DA FONTE — ex.: órgão responsável pelos registros de segurança pública]` |

> Os dados brutos são mantidos **sem alterações** em `data/raw/`. Toda transformação é feita por código e é rastreável.

---

## 📖 Dicionário de Variáveis (resumo)

O dicionário completo está em [`data/data_dictionary.md`](data/data_dictionary.md).

| Variável | Descrição | Tipo | Unidade |
|---|---|---|---|
| `ano` | Ano de referência do 1º quadrimestre | `int` | ano |
| `vitimas` | Nº de vítimas de autos de resistência no 1º quadrimestre | `int` | pessoas |
| `diferenca_absoluta` | Variação em relação ao mesmo período do ano anterior | `int` | pessoas |
| `diferenca_percentual` | Variação percentual em relação ao ano anterior | `float` | % |
| `taxa_100mil` | Vítimas por 100 mil habitantes | `float` | por 100 mil hab. |
| `media_mensal` | Média mensal de vítimas no quadrimestre (`vitimas / 4`) | `float` | pessoas/mês |

> *Os nomes de colunas acima seguem a nomenclatura padronizada (snake_case) adotada no ETL; devem ser conferidos com o arquivo bruto baixado.*

---

## 🗂️ Estrutura do Repositório

```
nome-do-projeto/
├── README.md                  # Este arquivo
├── LICENSE                    # Licença MIT (código)
├── requirements.txt           # Dependências com versões fixadas (pip freeze)
├── .gitignore
│
├── data/
│   ├── raw/                   # Dado bruto original, sem alterações
│   ├── processed/             # Dado tratado (.parquet / .csv.gz)
│   └── data_dictionary.md     # Dicionário de dados (FAIR)
│
├── notebooks/
│   └── analise_exploratoria.ipynb   # EDA, prototipação e validação
│
├── src/
│   ├── __init__.py
│   └── etl.py                 # Limpeza, validação e métricas
│
└── docs/                      # Artigo acadêmico (GitHub Pages)
    ├── index.html
    └── assets/                # Figuras e visualizações exportadas
```

---

## ⚙️ Pipeline de Dados (ETL)

1. **Aquisição:** leitura do arquivo bruto obtido no Data.Rio, com atenção a codificação (`utf-8`/`latin-1`), separador e formato numérico (vírgula decimal).
2. **Higienização:** padronização de nomes de colunas, conversão de tipos primitivos, tratamento de valores ausentes e remoção de linhas de cabeçalho/rodapé espúrias, sem operações destrutivas sobre `data/raw/`.
3. **Validação das métricas derivadas:**
   - `diferenca_absoluta = vitimas[t] − vitimas[t−1]`
   - `diferenca_percentual = (diferenca_absoluta / vitimas[t−1]) × 100`
   - `media_mensal = vitimas / 4`
   - `taxa_100mil = (vitimas / populacao) × 100.000`

   Os valores recalculados são comparados com os publicados na fonte, e as divergências são registradas.
4. **Persistência:** exportação para `data/processed/` em formato aberto (`.parquet` ou `.csv.gz`).

Exemplo de uso do módulo:

```python
from src.etl import carregar_bruto, limpar, validar_metricas, salvar

df = carregar_bruto("data/raw/autos_resistencia_1quad_2003_2022.csv")
df = limpar(df)
df = validar_metricas(df)
salvar(df, "data/processed/autos_resistencia_1quad.parquet")
```

---

## 📊 Visualizações

| Visualização | Tipo | Pergunta |
|---|---|---|
| Evolução do nº de vítimas por ano | Linha / barras | RQ1 |
| Taxa por 100 mil habitantes ao longo do tempo | Linha (Plotly interativo) | RQ2 |
| Variação percentual interanual | Barras divergentes | RQ3 |
| Comparação absoluto × taxa | Eixo duplo / painéis | RQ2 |

As figuras estão em [`docs/assets/`](docs/assets/) e embutidas no [artigo](https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/).

---

## 🚀 Como Reproduzir

**Pré-requisitos:** Python 3.11+ e Git.

```bash
# 1. Clonar o repositório
git clone https://github.com/SEU-USUARIO/NOME-DO-REPOSITORIO.git
cd NOME-DO-REPOSITORIO

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Instalar as dependências (versões fixadas)
pip install -r requirements.txt

# 4. Executar o pipeline de ETL
python -m src.etl

# 5. Abrir a análise exploratória
jupyter lab notebooks/analise_exploratoria.ipynb
```

Nenhuma etapa exige credenciais ou serviços pagos.

---

## ✅ Conformidade com os Princípios FAIR

| Princípio | Como é atendido |
|---|---|
| **Findable** | README com resumo, palavras-chave e link perene da fonte; autoria, disciplina, semestre e instituição identificados. |
| **Accessible** | Repositório público; scripts sem autenticação proprietária; artigo em GitHub Pages, responsivo. |
| **Interoperable** | `data/data_dictionary.md` completo; dados processados em formatos abertos (`.parquet` / `.csv.gz`). |
| **Reusable** | Licença MIT (código) e CC-BY 4.0 (dados e texto); `requirements.txt` com versões fixadas. |

---

## ⚠️ Limitações e Considerações Éticas

- Os dados representam **apenas o 1º quadrimestre** de cada ano e **não** permitem inferências sobre o ano completo.
- A classificação "auto de resistência" depende de **registro institucional** e pode estar sujeita a subnotificação ou a mudanças de critério ao longo da série.
- O tema envolve **mortes de pessoas**; a análise busca apresentar os números com rigor e sem sensacionalismo, e não implica juízo sobre casos individuais.
- A taxa por 100 mil habitantes depende das estimativas populacionais usadas pela fonte.

---

## 📚 Referências

- DATA.RIO. *Vítimas de auto de resistência, por diferença absoluta, diferença percentual, taxa por cem mil habitantes e média mensal, segundo o 1º quadrimestre de cada ano, no Município do Rio de Janeiro entre 2003 e 2022.* Prefeitura da Cidade do Rio de Janeiro. Disponível em: https://www.data.rio/documents/98961641129c4ee1aacd2445f82ac0ce/about. Acesso em: 9 nov. 2026.
- WILKINSON, M. D. et al. The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data*, v. 3, 160018, 2016. https://doi.org/10.1038/sdata.2016.18
- Documentação: [pandas](https://pandas.pydata.org/docs/) · [NumPy](https://numpy.org/doc/) · [Plotly](https://plotly.com/python/)

---

## 📄 Licença

- **Código-fonte:** [MIT](LICENSE)
- **Dados processados, texto e figuras:** [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br)

Os dados brutos permanecem sujeitos aos termos de uso do portal Data.Rio.

## 👥 Autores

| Nome | GitHub |
|---|---|
| `[Nome 1]` | [@usuario1](https://github.com/usuario1) |
| `[Nome 2]` | [@usuario2](https://github.com/usuario2) |
| `[Nome 3]` | [@usuario3](https://github.com/usuario3) |
