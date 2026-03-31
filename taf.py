import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CBMAM · Dashboard TAF",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0b1220 0%, #0f172a 100%);
    color: #e7eefc;
  }
  [data-testid="stSidebar"] {
    background: #111b2e;
    border-right: 1px solid rgba(255,255,255,.08);
  }
  [data-testid="metric-container"] {
    background: rgba(17,27,46,.8);
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 14px;
    padding: 18px 20px;
  }
  .section-title {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: .5px;
    color: #ef4444;
    margin: 28px 0 8px;
    border-left: 4px solid #ef4444;
    padding-left: 10px;
  }
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

DARK = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e7eefc")
GRID = dict(gridcolor="rgba(255,255,255,.06)")

COR_MAP = {
    "Excelente": "#22c55e",
    "Bom":       "#3b82f6",
    "Regular":   "#f59e0b",
    "Insuficiente": "#ef4444",
    "Ausente":   "#64748b",
}

ORDEM_POSTO = {
    "CEL": 1, "TC": 2, "MAJOR": 3, "CAP": 4,
    "1° TEN": 5, "2° TEN": 6, "ASP OF": 7,
    "ST": 8, "1° SGT": 9, "2° SGT": 10, "3° SGT": 11,
    "CB": 12, "SD": 13,
}

# Data de referência para cálculo da idade (data do BG)
DATA_REFERENCIA_TAF = datetime(2024, 1, 12)

# ══════════════════════════════════════════════════════════════════════════════
# TABELAS DE PONTUAÇÃO POR IDADE E SEXO (EXTRAÍDAS DO PDF)
# ══════════════════════════════════════════════════════════════════════════════

# Faixas etárias para homens e mulheres
FAIXAS_ETARIAS_MASC = [
    (18, 21), (22, 25), (26, 29), (30, 34), (35, 39),
    (40, 44), (45, 49), (50, 53), (54, 57), (58, 150) # 150 para ">58"
]
FAIXAS_ETARIAS_FEM = [
    (18, 21), (22, 25), (26, 29), (30, 34), (35, 39),
    (40, 44), (45, 49), (50, 53), (54, 57), (58, 150) # 150 para ">58"
]

# Dicionários para armazenar as tabelas de pontuação
# Chave: (sexo, faixa_etaria_min, faixa_etaria_max)
# Valor: DataFrame com as colunas de desempenho e notas
TABELAS_PONTUACAO = {}

# Tabela Masculina (extraída da PAGE 1 do PDF)
data_masc = {
    "Corrida": [3200, 3100, 3000, 2900, 2800, 2700, 2600, 2500, 2400, 2300, 2200, 2100, 2000, 1900, 1800, 1700, 1600, 1500],
    "Flexao": [38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21],
    "Abdominal": [48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31],
    "Barra_Din": [13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, np.nan, np.nan, np.nan, np.nan, np.nan], # - para np.nan
    "Barra_Est": [60, 57, 55, 53, 51, 49, 47, 45, 43, 41, 39, 37, 35, 33, 31, 29, 27, 25], # segundos
    "Natacao": [40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96, 100, 104, 108], # segundos
    "18-21": [10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5],
    "22-25": [10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2],
    "26-29": [10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3, 2.5],
    "30-34": [10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3],
    "35-39": [10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5],
    "40-44": [10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4],
    "45-49": [10, 10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5],
    "50-53": [10, 10, 10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5],
    "54-57": [10, 10, 10, 10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5],
    ">58": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6],
}
df_masc = pd.DataFrame(data_masc)

for i, (min_age, max_age) in enumerate(FAIXAS_ETARIAS_MASC):
    col_name = list(data_masc.keys())[6 + i] # Colunas de notas por faixa etária
    TABELAS_PONTUACAO[("M", min_age, max_age)] = df_masc[[
        "Corrida", "Flexao", "Abdominal", "Barra_Din", "Barra_Est", "Natacao", col_name
    ]].rename(columns={col_name: "Nota"})

# Tabela Feminina (extraída da PAGE 2 do PDF)
data_fem = {
    "Corrida": [2700, 2600, 2500, 2400, 2300, 2200, 2100, 2000, 1900, 1800, 1700, 1600, 1500, 1400, 1300, 1200, 1100, 1000],
    "Flexao": [30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13],
    "Abdominal": [42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25],
    "Barra_Din": [np.nan] * 18, # Feminino não tem barra dinâmica
    "Barra_Est": [50, 47, 45, 43, 41, 39, 37, 35, 33, 31, 29, 27, 25, 23, 21, 19, 17, 15], # segundos
    "Natacao": [54, 58, 62, 66, 70, 74, 78, 82, 86, 90, 94, 98, 102, 106, 110, 114, 122, 126], # segundos
    "18-21": [10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5],
    "22-25": [10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2],
    "26-29": [10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3, 2.5],
    "30-34": [10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5, 3],
    "35-39": [10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4, 3.5],
    "40-44": [10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5, 4],
    "45-49": [10, 10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.5],
    "50-53": [10, 10, 10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5, 5],
    "54-57": [10, 10, 10, 10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5],
    ">58": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6],
}
df_fem = pd.DataFrame(data_fem)

for i, (min_age, max_age) in enumerate(FAIXAS_ETARIAS_FEM):
    col_name = list(data_fem.keys())[6 + i]
    TABELAS_PONTUACAO[("F", min_age, max_age)] = df_fem[[
        "Corrida", "Flexao", "Abdominal", "Barra_Din", "Barra_Est", "Natacao", col_name
    ]].rename(columns={col_name: "Nota"})


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════

def parse_time(val):
    """Converte formatos de tempo como 01'04", 47", 1'09" para segundos."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if any(x in s.upper() for x in ["NÃO", "COMPARECEU", "APTO"]):
        return np.nan
    s = s.replace('"', "'").replace("''", "'").strip("'").strip()
    m = re.match(r"^0*(\d+)'(\d+)$", s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.match(r"^(\d+)$", s)
    if m:
        return int(m.group(1))
    return np.nan


def classificar_barra_tipo(val_raw):
    """Classifica se o valor da barra é dinâmica (reps) ou estática (tempo)."""
    if pd.isna(val_raw):
        return None
    s = str(val_raw).strip()
    if any(x in s.upper() for x in ["NÃO", "COMPARECEU"]):
        return None
    if "'" in s or '"' in s:
        return "ESTATICA"
    try:
        float(s)
        return "DINAMICA"
    except ValueError:
        return None

def calcular_idade(data_nascimento, data_referencia):
    """Calcula a idade em anos completos na data de referência."""
    if pd.isna(data_nascimento):
        return np.nan
    data_nascimento = pd.to_datetime(data_nascimento)
    idade = data_referencia.year - data_nascimento.year - ((data_referencia.month, data_referencia.day) < (data_nascimento.month, data_nascimento.day))
    return idade

def obter_tabela_pontuacao(sexo, idade):
    """Retorna a tabela de pontuação para o sexo e idade dados."""
    if pd.isna(sexo) or pd.isna(idade):
        return None

    faixas = FAIXAS_ETARIAS_MASC if sexo == "M" else FAIXAS_ETARIAS_FEM
    for min_age, max_age in faixas:
        if min_age <= idade <= max_age:
            return TABELAS_PONTUACAO.get((sexo, min_age, max_age))
    return None

# ── Funções de Pontuação TAF (AGORA COM IDADE E SEXO) ───────────────────────

def nota_corrida(metros, sexo, idade):
    if pd.isna(metros) or pd.isna(sexo) or pd.isna(idade): return np.nan
    tabela = obter_tabela_pontuacao(sexo, idade)
    if tabela is None: return np.nan

    # Para corrida, queremos a maior nota para o maior desempenho (metros)
    # A tabela está em ordem decrescente de metros, então a primeira linha que atende é a nota máxima
    for _, row in tabela.sort_values(by="Corrida", ascending=False).iterrows():
        if metros >= row["Corrida"]:
            return row["Nota"]
    return tabela["Nota"].min() # Se não atingiu o mínimo da tabela, retorna a nota mais baixa ou 0


def nota_abdominal(reps, sexo, idade):
    if pd.isna(reps) or pd.isna(sexo) or pd.isna(idade): return np.nan
    tabela = obter_tabela_pontuacao(sexo, idade)
    if tabela is None: return np.nan

    for _, row in tabela.sort_values(by="Abdominal", ascending=False).iterrows():
        if reps >= row["Abdominal"]:
            return row["Nota"]
    return tabela["Nota"].min()


def nota_flexao(reps, sexo, idade):
    if pd.isna(reps) or pd.isna(sexo) or pd.isna(idade): return np.nan
    tabela = obter_tabela_pontuacao(sexo, idade)
    if tabela is None: return np.nan

    for _, row in tabela.sort_values(by="Flexao", ascending=False).iterrows():
        if reps >= row["Flexao"]:
            return row["Nota"]
    return tabela["Nota"].min()


def nota_natacao(segs, sexo, idade):
    if pd.isna(segs) or pd.isna(sexo) or pd.isna(idade): return np.nan
    tabela = obter_tabela_pontuacao(sexo, idade)
    if tabela is None: return np.nan

    # Para natação, queremos a maior nota para o menor tempo (segs)
    # A tabela está em ordem crescente de segundos, então a primeira linha que atende é a nota máxima
    for _, row in tabela.sort_values(by="Natacao", ascending=True).iterrows():
        if segs <= row["Natacao"]:
            return row["Nota"]
    return tabela["Nota"].min() # Se o tempo for muito alto, retorna a nota mais baixa ou 0


def nota_barra_din(reps, sexo, idade):
    if pd.isna(reps) or pd.isna(sexo) or pd.isna(idade): return np.nan
    tabela = obter_tabela_pontuacao(sexo, idade)
    if tabela is None or "Barra_Din" not in tabela.columns: return np.nan # Feminino não tem barra dinâmica

    for _, row in tabela.sort_values(by="Barra_Din", ascending=False).iterrows():
        if pd.notna(row["Barra_Din"]) and reps >= row["Barra_Din"]:
            return row["Nota"]
    return tabela["Nota"].min()


def nota_barra_est(segs, sexo, idade):
    if pd.isna(segs) or pd.isna(sexo) or pd.isna(idade): return np.nan
    tabela = obter_tabela_pontuacao(sexo, idade)
    if tabela is None or "Barra_Est" not in tabela.columns: return np.nan

    # Para barra estática, queremos a maior nota para o maior tempo (segs)
    for _, row in tabela.sort_values(by="Barra_Est", ascending=False).iterrows():
        if pd.notna(row["Barra_Est"]) and segs >= row["Barra_Est"]:
            return row["Nota"]
    return tabela["Nota"].min()


def classificar_media(m):
    if pd.isna(m): return "Ausente"
    if m >= 9.0: return "Excelente"
    if m >= 7.5: return "Bom"
    if m >= 6.0: return "Regular"
    return "Insuficiente"


def normalizar_posto(p):
    """Normaliza variações de posto/graduação (º vs °)."""
    s = str(p).strip().upper()
    s = s.replace("º", "°")
    return s


def ordem_posto(p):
    return ORDEM_POSTO.get(p, 99)


# ══════════════════════════════════════════════════════════════════════════════
# CARREGAMENTO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def carregar_dados():
    """Carrega e processa o TAF.csv — seção Regular (TAF completo)."""
    df_raw = pd.read_csv("TAF.csv", header=None, encoding="utf-8-sig", dtype=str)

    # Carregar taf_indices.csv para id, data_taf, sexo
    df_indices = pd.read_csv("taf_indices.csv", encoding="utf-8-sig", dtype=str)
    df_indices["id"] = df_indices["id"].astype(str).str.strip().str.upper()
    df_indices["sexo"] = df_indices["sexo"].astype(str).str.strip().str.upper()
    df_indices["data_taf"] = pd.to_datetime(df_indices["data_taf"], errors="coerce")

    # Encontrar marcadores de seção
    headers = []
    adapted_marker = None
    for i in range(len(df_raw)):
        cell = str(df_raw.iloc[i, 0]).strip()
        if cell == "ORD":
            headers.append(i)
        if "TAF ADAPTADO" in cell:
            adapted_marker = i

    # Seções regulares: antes do TAF ADAPTADO
    regular_headers = [h for h in headers if adapted_marker is None or h < adapted_marker]

    sections = []
    for idx, h in enumerate(regular_headers):
        if idx + 1 < len(regular_headers):
            end = regular_headers[idx + 1] - 3
        elif adapted_marker:
            end = adapted_marker
        else:
            end = len(df_raw)

        section = df_raw.iloc[h + 1:end].copy()
        section = section[section.iloc[:, 0].notna()]
        section = section[~section.iloc[:, 0].astype(str).str.strip().isin(["", "nan"])]
        section = section[~section.iloc[:, 0].astype(str).str.contains(
            r"TAF|FALTOU|MILITARES|^B$|^A$|DESEMPENHO", case=False, na=False
        )]
        section = section[pd.to_numeric(section.iloc[:, 0], errors="coerce").notna()]
        sections.append(section)

    df = pd.concat(sections, ignore_index=True)
    df = df.iloc[:, :9]
    df.columns = ["ORD", "POSTO_GRAD", "QUADRO", "NOME",
                  "CORRIDA_RAW", "ABDOMINAL_RAW", "FLEXAO_RAW",
                  "NATACAO_RAW", "BARRA_RAW"]

    # Limpar strings
    df["NOME"] = df["NOME"].astype(str).str.strip().str.upper()
    df["POSTO_GRAD"] = df["POSTO_GRAD"].astype(str).apply(normalizar_posto)
    df["QUADRO"] = df["QUADRO"].astype(str).str.strip().str.upper()
    df["ORD"] = pd.to_numeric(df["ORD"], errors="coerce").astype("Int64")

    # Unir com df_indices para obter id, data_taf e sexo
    # Assumindo que 'NOME' pode ser usado para junção, ou que 'id' pode ser inferido/adicionado
    # Para este exemplo, vamos assumir que o 'id' do taf_indices.csv corresponde a um identificador único no TAF.csv
    # Se 'NOME' não for único, precisaremos de um 'id' no TAF.csv também.
    # Por simplicidade, vou tentar juntar por nome, mas o ideal seria um ID único.
    df = pd.merge(df, df_indices, left_on="NOME", right_on="id", how="left", suffixes=('', '_indices'))
    # Se o 'id' do taf_indices for o nome, podemos renomear para evitar confusão
    df['id'] = df['id'].fillna(df['NOME']) # Usa o nome como ID se não houver um ID explícito
    df = df.drop(columns=['id_indices'], errors='ignore') # Remove coluna duplicada se houver

    # Calcular idade
    df["IDADE"] = df["data_taf"].apply(lambda x: calcular_idade(x, DATA_REFERENCIA_TAF))

    # Marcar presentes/ausentes
    df["PRESENTE"] = ~df["CORRIDA_RAW"].astype(str).str.upper().str.contains(
        "NÃO COMPARECEU", na=False
    )

    # Parsear valores brutos
    df["CORRIDA"] = pd.to_numeric(
        df["CORRIDA_RAW"].astype(str).str.replace(",", ".", regex=False).str.strip(),
        errors="coerce"
    )
    df.loc[df["CORRIDA"] > 5000, "CORRIDA"] = df.loc[df["CORRIDA"] > 5000, "CORRIDA"] / 10
    df["ABDOMINAL"] = pd.to_numeric(df["ABDOMINAL_RAW"], errors="coerce")
    df["FLEXAO"] = pd.to_numeric(df["FLEXAO_RAW"], errors="coerce")
    df["NATACAO_SEG"] = df["NATACAO_RAW"].apply(parse_time)
    df["BARRA_TIPO"] = df["BARRA_RAW"].apply(classificar_barra_tipo)
    df["BARRA_VALOR"] = df["BARRA_RAW"].apply(parse_time) # Para barra estática (tempo)
    # Para barra dinâmica (reps), o valor já é numérico em FLEXAO_RAW, mas o parse_time pode ser usado se for string
    # Vamos ajustar BARRA_VALOR para lidar com reps e tempo
    df.loc[df["BARRA_TIPO"] == "DINAMICA", "BARRA_VALOR"] = pd.to_numeric(
        df.loc[df["BARRA_TIPO"] == "DINAMICA", "BARRA_RAW"], errors="coerce"
    )


    # Calcular notas usando idade e sexo
    df["NOTA_CORRIDA"] = df.apply(lambda row: nota_corrida(row["CORRIDA"], row["sexo"], row["IDADE"]), axis=1)
    df["NOTA_ABDOMINAL"] = df.apply(lambda row: nota_abdominal(row["ABDOMINAL"], row["sexo"], row["IDADE"]), axis=1)
    df["NOTA_FLEXAO"] = df.apply(lambda row: nota_flexao(row["FLEXAO"], row["sexo"], row["IDADE"]), axis=1)
    df["NOTA_NATACAO"] = df.apply(lambda row: nota_natacao(row["NATACAO_SEG"], row["sexo"], row["IDADE"]), axis=1)

    df["NOTA_BARRA"] = np.nan
    mask_din = df["BARRA_TIPO"] == "DINAMICA"
    mask_est = df["BARRA_TIPO"] == "ESTATICA"
    df.loc[mask_din, "NOTA_BARRA"] = df.loc[mask_din].apply(
        lambda row: nota_barra_din(row["BARRA_VALOR"], row["sexo"], row["IDADE"]), axis=1
    )
    df.loc[mask_est, "NOTA_BARRA"] = df.loc[mask_est].apply(
        lambda row: nota_barra_est(row["BARRA_VALOR"], row["sexo"], row["IDADE"]), axis=1
    )

    # Média final
    nota_cols = ["NOTA_CORRIDA", "NOTA_ABDOMINAL", "NOTA_FLEXAO", "NOTA_NATACAO", "NOTA_BARRA"]
    df["MEDIA_FINAL"] = df[nota_cols].mean(axis=1)
    df["CLASSIFICACAO"] = df["MEDIA_FINAL"].apply(classificar_media)

    # Ponto fraco e forte
    notas_map = {
        "Corrida 12min": "NOTA_CORRIDA",
        "Abdominal": "NOTA_ABDOMINAL",
        "Flexão": "NOTA_FLEXAO",
        "Natação 50m": "NOTA_NATACAO",
        "Barra": "NOTA_BARRA",
    }

    def ponto_fraco(row):
        vals = {k: float(row[v]) for k, v in notas_map.items() if pd.notna(row[v])}
        return min(vals, key=vals.get) if vals else "—"

    def ponto_forte(row):
        vals = {k: float(row[v]) for k, v in notas_map.items() if pd.notna(row[v])}
        return max(vals, key=vals.get) if vals else "—"

    df["PONTO_FRACO"] = df.apply(ponto_fraco, axis=1)
    df["PONTO_FORTE"] = df.apply(ponto_forte, axis=1)

    return df, notas_map


@st.cache_data
def carregar_adaptado():
    """Carrega e processa o TAF.csv — seção TAF Adaptado."""
    df_raw = pd.read_csv("TAF.csv", header=None, encoding="utf-8-sig", dtype=str)

    adapted_marker = None
    adapted_header = None
    for i in range(len(df_raw)):
        cell = str(df_raw.iloc[i, 0]).strip()
        if "TAF ADAPTADO" in cell:
            adapted_marker = i
        if cell == "ORD" and adapted_marker is not None:
            adapted_header = i
            break

    if adapted_header is None:
        return pd.DataFrame()

    df = df_raw.iloc[adapted_header + 1:].copy()
    df = df[df.iloc[:, 0].notna()]
    df = df[pd.to_numeric(df.iloc[:, 0], errors="coerce").notna()]

    cols = ["ORD", "POSTO_GRAD", "QUADRO", "NOME", "CAMINHADA", "ABDOMINAL",
            "FLEXAO", "PRANCHA", "NATACAO", "BARRA_EST", "BARRA_DIN",
            "CORRIDA", "PUXADOR_FRONTAL", "FLUTUACAO", "SUPINO", "COOPER"]
    df = df.iloc[:, :min(16, df.shape[1])]
    while len(df.columns) < 16:
        df[f"_pad_{len(df.columns)}"] = np.nan
    df.columns = cols[:len(df.columns)]

    df["NOME"] = df["NOME"].astype(str).str.strip().str.upper()
    df["POSTO_GRAD"] = df["POSTO_GRAD"].astype(str).apply(normalizar_posto)
    df["QUADRO"] = df["QUADRO"].astype(str).str.strip().str.upper()
    df["PRESENTE"] = ~df["CAMINHADA"].astype(str).str.upper().str.contains(
        "NÃO COMPARECEU", na=False
    )
    return df


# ══════════════════════════════════════════════════════════════════════════════
# CARREGAR DADOS
# ══════════════════════════════════════════════════════════════════════════════
df_all, notas_map = carregar_dados()
df_adaptado = carregar_adaptado()

colunas_nota = list(notas_map.values())
labels_nota = list(notas_map.keys())
cats_radar = labels_nota + [labels_nota[0]]


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/"
        "Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Amazonas.svg/"
        "200px-Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Amazonas.svg.png",
        width=80,
    )
    st.markdown("## CBMAM · TAF 2026")
    st.markdown("**Análise de Desempenho Físico**")
    st.divider()

    pagina = st.radio(
        "📌 Navegação",
        [
            "🏠 Visão Geral",
            "🪖 Por Posto/Graduação",
            "📋 Por Quadro",
            "👤 Ficha Individual",
            "📈 Estatísticas",
            "♿ TAF Adaptado",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # Filtros globais
    if pagina not in ["👤 Ficha Individual", "♿ TAF Adaptado"]:
        st.markdown("**🔧 Filtros**")

        # Filtro de Ano (placeholder, pois só temos um ano de dados no momento)
        anos_disponiveis = sorted(df_all["data_taf"].dt.year.dropna().unique().tolist(), reverse=True)
        if len(anos_disponiveis) > 1:
            filtro_ano = st.multiselect("Ano do TAF", anos_disponiveis, default=anos_disponiveis)
        else:
            filtro_ano = anos_disponiveis # Se só tem um ano, seleciona ele automaticamente
            st.info(f"Ano do TAF: {anos_disponiveis[0] if anos_disponiveis else 'N/A'}")


        postos_disponiveis = sorted(
            df_all[df_all["PRESENTE"]]["POSTO_GRAD"].unique().tolist(),
            key=lambda x: ordem_posto(x),
        )
        filtro_posto = st.multiselect("Posto/Graduação", postos_disponiveis,
                                       default=postos_disponiveis)

        quadros_disponiveis = sorted(df_all[df_all["PRESENTE"]]["QUADRO"].unique().tolist())
        filtro_quadro = st.multiselect("Quadro", quadros_disponiveis,
                                        default=quadros_disponiveis)

        sexos_disponiveis = sorted(df_all["sexo"].dropna().unique().tolist())
        filtro_sexo = st.multiselect("Sexo", sexos_disponiveis, default=sexos_disponiveis)

        mostrar_ausentes = st.checkbox("Incluir ausentes", value=False)

        nota_minima = st.slider("Média mínima", 0.0, 10.0, 0.0, 0.1)
    else:
        filtro_ano = df_all["data_taf"].dt.year.dropna().unique().tolist()
        filtro_posto = df_all["POSTO_GRAD"].unique().tolist()
        filtro_quadro = df_all["QUADRO"].unique().tolist()
        filtro_sexo = df_all["sexo"].dropna().unique().tolist()
        mostrar_ausentes = False
        nota_minima = 0.0

    st.divider()
    efetivo_total = len(df_all)
    presentes_total = int(df_all["PRESENTE"].sum())
    st.markdown(
        f"<small>Efetivo: {efetivo_total} · Presentes: {presentes_total}<br>"
        f"CBMAM · BM-6/EMG · 2026</small>",
        unsafe_allow_html=True,
    )


# ── Filtrar dados ────────────────────────────────────────────────────────────
df_f = df_all.copy()
if not mostrar_ausentes:
    df_f = df_f[df_f["PRESENTE"]]

if filtro_ano:
    df_f = df_f[df_f["data_taf"].dt.year.isin(filtro_ano)]

df_f = df_f[df_f["POSTO_GRAD"].isin(filtro_posto)]
df_f = df_f[df_f["QUADRO"].isin(filtro_quadro)]
df_f = df_f[df_f["sexo"].isin(filtro_sexo)]
df_f = df_f[df_f["MEDIA_FINAL"].fillna(0) >= nota_minima]

# Dados apenas de presentes para cálculos
df_presentes = df_f[df_f["PRESENTE"] & df_f["MEDIA_FINAL"].notna()]


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "🏠 Visão Geral":

    col_txt, col_img = st.columns([2.2, 1])
    with col_txt:
        st.markdown("""
        <h1 style="margin:0;font-size:2rem;">🔥 Dashboard TAF · CBMAM</h1>
        <p style="margin:6px 0 12px;color:#94a3b8;">
          Corpo de Bombeiros Militar do Amazonas · Avaliação Física 2026
        </p>
        """, unsafe_allow_html=True)
        st.markdown("""
        > **Análise completa do Teste de Aptidão Física** com dados de desempenho
        > em corrida, abdominal, flexão, natação e barra. Filtre por posto/graduação,
        > quadro, sexo e ano para uma visão detalhada.
        """)

    with col_img:
        foto = Path("japura.enc")
        if foto.exists():
            st.image(str(foto), caption="CBMAM · 2026", use_container_width=True)

    st.divider()

    # KPIs
    st.markdown('<p class="section-title">📊 Indicadores Gerais</p>',
                unsafe_allow_html=True)

    if len(df_presentes) > 0:
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        media_geral = df_presentes["MEDIA_FINAL"].mean()
        melhor = df_presentes.loc[df_presentes["MEDIA_FINAL"].idxmax()]
        pior = df_presentes.loc[df_presentes["MEDIA_FINAL"].idxmin()]
        n_excelentes = len(df_presentes[df_presentes["CLASSIFICACAO"] == "Excelente"])
        n_insuficientes = len(df_presentes[df_presentes["CLASSIFICACAO"] == "Insuficiente"])
        n_ausentes = len(df_all[~df_all["PRESENTE"]])

        k1.metric("👥 Presentes", len(df_presentes))
        k2.metric("📈 Média Geral", f"{media_geral:.2f}")
        k3.metric("🥇 Maior Média", f"{melhor['MEDIA_FINAL']:.1f}",
                   melhor["NOME"].split()[0])
        k4.metric("⚠️ Menor Média", f"{pior['MEDIA_FINAL']:.1f}",
                   pior["NOME"].split()[0])
        k5.metric("✅ Excelentes", n_excelentes)
        k6.metric("🚨 Insuficientes / Ausentes", f"{n_insuficientes} / {n_ausentes}")

        st.divider()

        # Ranking
        st.markdown('<p class="section-title">🏆 Ranking — Média Final</p>',
                    unsafe_allow_html=True)

        df_rank = df_presentes.sort_values("MEDIA_FINAL", ascending=True).copy()
        df_rank["LABEL"] = df_rank.apply(
            lambda r: f"{r['POSTO_GRAD']} {' '.join(str(r['NOME']).split()[:2])}", axis=1
        )

        fig_rank = px.bar(
            df_rank, x="MEDIA_FINAL", y="LABEL", orientation="h",
            color="CLASSIFICACAO", color_discrete_map=COR_MAP,
            text="MEDIA_FINAL",
            hover_data={"NOME": True, "MEDIA_FINAL": True, "CLASSIFICACAO": True,
                       "POSTO_GRAD": True, "QUADRO": True, "sexo": True, "IDADE": True},
            labels={"MEDIA_FINAL": "Média Final", "LABEL": ""},
        )
        fig_rank.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_rank.update_layout(
            **DARK, height=max(500, len(df_rank) * 20),
            legend_title_text="Classificação",
            xaxis=dict(range=[0, 11], **GRID),
            yaxis=dict(**GRID),
            margin=dict(l=10, r=60, t=20, b=20),
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        # Distribuição
        st.markdown('<p class="section-title">📉 Distribuição de Desempenho</p>',
                    unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            contagem = df_presentes["CLASSIFICACAO"].value_counts().reset_index()
            contagem.columns = ["Classificação", "Quantidade"]
            ordem = ["Excelente", "Bom", "Regular", "Insuficiente"]
            contagem["Classificação"] = pd.Categorical(
                contagem["Classificação"], categories=ordem, ordered=True
            )
            fig_pie = px.pie(
                contagem.sort_values("Classificação"),
                names="Classificação", values="Quantidade",
                color="Classificação", color_discrete_map=COR_MAP,
                hole=0.52, title="Proporção por Classificação",
            )
            fig_pie.update_layout(
                **DARK,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                margin=dict(t=50, b=10),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            fig_hist = px.histogram(
                df_presentes, x="MEDIA_FINAL", nbins=15,
                color_discrete_sequence=["#3b82f6"],
                title="Histograma de Médias",
                labels={"MEDIA_FINAL": "Média Final", "count": "Frequência"},
            )
            fig_hist.add_vline(
                x=media_geral, line_dash="dash", line_color="#ef4444",
                annotation_text=f"Média: {media_geral:.2f}",
                annotation_font_color="#ef4444",
            )
            fig_hist.update_layout(
                **DARK, margin=dict(t=50, b=10),
                yaxis=dict(**GRID), xaxis=dict(**GRID),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        # Desempenho por disciplina
        st.markdown('<p class="section-title">💪 Desempenho Médio por Disciplina</p>',
                    unsafe_allow_html=True)

        medias_disc = {l: df_presentes[c].mean() for l, c in notas_map.items()}
        df_disc = pd.DataFrame({
            "Disciplina": list(medias_disc.keys()),
            "Média": list(medias_disc.values()),
        }).sort_values("Média")

        fig_disc = px.bar(
            df_disc, x="Média", y="Disciplina", orientation="h", text="Média",
            color_discrete_sequence=["#3b82f6"],
            title="Nota média por exercício",
        )
        fig_disc.update_traces(texttemplate="%{text:.2f}", textposition="outside",
                               showlegend=False)
        fig_disc.update_layout(
            **DARK, height=320,
            xaxis=dict(range=[0, 11], **GRID),
            yaxis=dict(**GRID),
            margin=dict(l=10, r=70, t=50, b=20),
        )
        st.plotly_chart(fig_disc, use_container_width=True)

        disc_pior = df_disc.iloc[0]
        disc_melhor = df_disc.iloc[-1]
        st.info(
            f"**📌 Insight:** A disciplina com menor média é "
            f"**{disc_pior['Disciplina']}** ({disc_pior['Média']:.2f}). "
            f"O ponto forte é **{disc_melhor['Disciplina']}** ({disc_melhor['Média']:.2f})."
        )

        # Radar Top 5 vs Bottom 5
        st.markdown('<p class="section-title">🕸️ Radar — Top 5 vs Bottom 5</p>',
                    unsafe_allow_html=True)

        top5 = df_presentes.nlargest(5, "MEDIA_FINAL")[colunas_nota].mean().tolist()
        bottom5 = df_presentes.nsmallest(5, "MEDIA_FINAL")[colunas_nota].mean().tolist()

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=top5 + [top5[0]], theta=cats_radar, fill="toself", name="Top 5",
            line_color="#22c55e", fillcolor="rgba(34,197,94,.15)",
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=bottom5 + [bottom5[0]], theta=cats_radar, fill="toself", name="Bottom 5",
            line_color="#ef4444", fillcolor="rgba(239,68,68,.15)",
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 10],
                                gridcolor="rgba(255,255,255,.12)",
                                tickfont_color="#94a3b8"),
                angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
            ),
            **DARK,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
            height=420, title="Comparativo — Top 5 vs Bottom 5",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # Mapa de calor
        st.markdown('<p class="section-title">🌡️ Mapa de Calor — Notas</p>',
                    unsafe_allow_html=True)

        df_heat = df_presentes[["NOME", "POSTO_GRAD"] + colunas_nota].copy()
        df_heat["LABEL"] = df_heat.apply(
            lambda r: f"{r['POSTO_GRAD']} {' '.join(str(r['NOME']).split()[:2])}", axis=1
        )
        df_heat = df_heat.sort_values("NOTA_CORRIDA", ascending=False)

        z_vals = df_heat[colunas_nota].values.tolist()
        fig_heat = go.Figure(go.Heatmap(
            z=z_vals, x=labels_nota, y=df_heat["LABEL"].tolist(),
            colorscale=[[0, "#ef4444"], [0.5, "#f59e0b"], [0.75, "#3b82f6"], [1, "#22c55e"]],
            zmin=0, zmax=10,
            text=[[f"{v:.1f}" if pd.notna(v) else "—" for v in row] for row in z_vals],
            texttemplate="%{text}",
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>",
            colorbar=dict(title="Nota", tickfont_color="#e7eefc",
                         title_font_color="#e7eefc"),
        ))
        fig_heat.update_layout(
            **DARK, height=max(500, len(df_heat) * 20),
            margin=dict(l=10, r=10, t=20, b=20),
            xaxis=dict(side="top"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # Pontos fracos
        st.markdown('<p class="section-title">🔍 Disciplinas com Mais Pontos Fracos</p>',
                    unsafe_allow_html=True)

        pf_df = df_presentes["PONTO_FRACO"].value_counts().reset_index()
        pf_df.columns = ["Disciplina", "Quantidade"]

        fig_pf = px.bar(
            pf_df, x="Disciplina", y="Quantidade",
            color="Quantidade",
            color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
            text="Quantidade", title="Disciplina com pior nota individual",
        )
        fig_pf.update_traces(textposition="outside")
        fig_pf.update_layout(
            **DARK, coloraxis_showscale=False,
            yaxis=dict(**GRID), xaxis=dict(**GRID),
            margin=dict(t=50, b=20), height=350,
        )
        st.plotly_chart(fig_pf, use_container_width=True)

        if len(pf_df) > 0:
            st.warning(
                f"⚠️ **{pf_df.iloc[0]['Quantidade']} militares** têm pior desempenho em "
                f"**{pf_df.iloc[0]['Disciplina']}**. Recomenda-se treino focado."
            )

        # Tabela
        st.markdown('<p class="section-title">📋 Tabela Completa</p>',
                    unsafe_allow_html=True)

        df_display = df_presentes[[
            "ORD", "POSTO_GRAD", "QUADRO", "NOME", "sexo", "IDADE",
            "NOTA_CORRIDA", "NOTA_ABDOMINAL", "NOTA_FLEXAO",
            "NOTA_NATACAO", "NOTA_BARRA", "MEDIA_FINAL",
            "CLASSIFICACAO", "PONTO_FRACO",
        ]].rename(columns={
            "ORD": "Nº", "POSTO_GRAD": "Posto", "QUADRO": "Quadro",
            "NOTA_CORRIDA": "Corrida", "NOTA_ABDOMINAL": "Abdominal",
            "NOTA_FLEXAO": "Flexão", "NOTA_NATACAO": "Natação",
            "NOTA_BARRA": "Barra", "MEDIA_FINAL": "Média",
            "CLASSIFICACAO": "Status", "PONTO_FRACO": "Ponto Fraco",
            "sexo": "Sexo", "IDADE": "Idade"
        })

        def colorir(val):
            try:
                v = float(val)
            except (ValueError, TypeError):
                return ""
            if v >= 9.0: return "background-color:rgba(34,197,94,.25);color:#bbf7d0"
            if v >= 7.5: return "background-color:rgba(59,130,246,.25);color:#bfdbfe"
            if v >= 6.0: return "background-color:rgba(245,158,11,.25);color:#fde68a"
            return "background-color:rgba(239,68,68,.25);color:#fecaca"

        st.dataframe(
            df_display.style.map(colorir, subset=["Média"]),
            use_container_width=True, height=420,
        )

        # Conclusões
        st.divider()
        st.markdown('<p class="section-title">💡 Conclusões e Recomendações</p>',
                    unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            #### 🎯 Treinamento direcionado
            Intensificar treinos na disciplina com menor média coletiva.
            Um programa semanal específico pode elevar o desempenho
            geral em até 15% em 3 meses.
            """)
        with c2:
            st.markdown("""
            #### 📅 Monitoramento contínuo
            Aplicar o TAF a cada bimestre para acompanhar evolução
            individual e detectar regressões antes de nível crítico.
            """)
        with c3:
            st.markdown("""
            #### 🤝 Mentoria entre pares
            Militares *Excelente* podem apoiar os de *Insuficiente* em
            sessões conjuntas, fortalecendo o espírito de equipe.
            """)

    else:
        st.warning("Nenhum militar encontrado com os filtros atuais.")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: POR POSTO/GRADUAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🪖 Por Posto/Graduação":
    st.markdown("""
    <h1 style="margin:0;font-size:2rem;">🪖 Análise por Posto/Graduação</h1>
    <p style="margin:6px 0 12px;color:#94a3b8;">
      Comparativo de desempenho entre os diferentes postos e graduações
    </p>
    """, unsafe_allow_html=True)
    st.divider()

    if len(df_presentes) == 0:
        st.warning("Nenhum dado disponível com os filtros atuais.")
    else:
        # Tabela resumo
        st.markdown('<p class="section-title">📊 Resumo por Posto/Graduação</p>',
                    unsafe_allow_html=True)

        resumo = df_presentes.groupby("POSTO_GRAD").agg(
            Efetivo=("NOME", "count"),
            Media=("MEDIA_FINAL", "mean"),
            Mediana=("MEDIA_FINAL", "median"),
            Minimo=("MEDIA_FINAL", "min"),
            Maximo=("MEDIA_FINAL", "max"),
            Desvio=("MEDIA_FINAL", "std"),
        ).reset_index()
        resumo["_ordem"] = resumo["POSTO_GRAD"].apply(ordem_posto)
        resumo = resumo.sort_values("_ordem").drop(columns=["_ordem"])
        resumo.columns = ["Posto/Grad", "Efetivo", "Média", "Mediana",
                          "Mínimo", "Máximo", "Desvio Padrão"]
        for c in ["Média", "Mediana", "Mínimo", "Máximo", "Desvio Padrão"]:
            resumo[c] = resumo[c].round(2)
        st.dataframe(resumo, use_container_width=True, hide_index=True)

        # Média por posto
        st.markdown('<p class="section-title">📈 Média por Posto/Graduação</p>',
                    unsafe_allow_html=True)

        df_posto_media = df_presentes.groupby("POSTO_GRAD")["MEDIA_FINAL"].mean().reset_index()
        df_posto_media["_ordem"] = df_posto_media["POSTO_GRAD"].apply(ordem_posto)
        df_posto_media = df_posto_media.sort_values("_ordem")

        fig_posto = px.bar(
            df_posto_media, x="POSTO_GRAD", y="MEDIA_FINAL",
            color="MEDIA_FINAL",
            color_continuous_scale=["#ef4444", "#f59e0b", "#3b82f6", "#22c55e"],
            text="MEDIA_FINAL",
            labels={"POSTO_GRAD": "Posto/Graduação", "MEDIA_FINAL": "Média"},
            title="Média final por posto/graduação",
        )
        fig_posto.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_posto.update_layout(
            **DARK, height=400, coloraxis_showscale=False,
            xaxis=dict(**GRID), yaxis=dict(range=[0, 11], **GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_posto, use_container_width=True)

        # Box plot
        st.markdown('<p class="section-title">📦 Distribuição por Posto/Graduação</p>',
                    unsafe_allow_html=True)

        df_box = df_presentes.copy()
        df_box["_ordem"] = df_box["POSTO_GRAD"].apply(ordem_posto)
        df_box = df_box.sort_values("_ordem")

        fig_box = px.box(
            df_box, x="POSTO_GRAD", y="MEDIA_FINAL",
            color="POSTO_GRAD",
            labels={"POSTO_GRAD": "Posto/Graduação", "MEDIA_FINAL": "Média Final"},
            title="Distribuição da média final por posto",
        )
        fig_box.update_layout(
            **DARK, height=450, showlegend=False,
            xaxis=dict(**GRID), yaxis=dict(**GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_box, use_container_width=True)

        # Classificação por posto (stacked bar)
        st.markdown('<p class="section-title">📊 Classificação por Posto</p>',
                    unsafe_allow_html=True)

        class_posto = df_presentes.groupby(
            ["POSTO_GRAD", "CLASSIFICACAO"]
        ).size().reset_index(name="Qtd")
        class_posto["_ordem"] = class_posto["POSTO_GRAD"].apply(ordem_posto)
        class_posto = class_posto.sort_values("_ordem")

        fig_stack = px.bar(
            class_posto, x="POSTO_GRAD", y="Qtd", color="CLASSIFICACAO",
            color_discrete_map=COR_MAP, barmode="stack",
            labels={"POSTO_GRAD": "Posto/Graduação", "Qtd": "Quantidade"},
            title="Distribuição de classificações por posto",
        )
        fig_stack.update_layout(
            **DARK, height=400,
            xaxis=dict(**GRID), yaxis=dict(**GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_stack, use_container_width=True)

        # Radar comparativo dos postos
        st.markdown('<p class="section-title">🕸️ Radar Comparativo por Posto</p>',
                    unsafe_allow_html=True)

        postos_top = df_posto_media.head(6)["POSTO_GRAD"].tolist()
        cores_radar = ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#a855f7", "#ec4899"]
        fig_radar_posto = go.Figure()
        for idx, posto in enumerate(postos_top):
            vals = df_presentes[df_presentes["POSTO_GRAD"] == posto][colunas_nota].mean().tolist()
            fig_radar_posto.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=cats_radar,
                name=posto, line_color=cores_radar[idx % len(cores_radar)],
            ))
        fig_radar_posto.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 10],
                                gridcolor="rgba(255,255,255,.12)",
                                tickfont_color="#94a3b8"),
                angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
            ),
            **DARK, height=450,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            title="Perfil de desempenho por posto",
        )
        st.plotly_chart(fig_radar_posto, use_container_width=True)

        # Taxa de ausência por posto
        st.markdown('<p class="section-title">📋 Taxa de Ausência por Posto</p>',
                    unsafe_allow_html=True)

        ausencia = df_all.groupby("POSTO_GRAD").agg(
            Total=("NOME", "count"),
            Ausentes=("PRESENTE", lambda x: (~x).sum()),
        ).reset_index()
        ausencia["Taxa (%)"] = (ausencia["Ausentes"] / ausencia["Total"] * 100).round(1)
        ausencia["_ordem"] = ausencia["POSTO_GRAD"].apply(ordem_posto)
        ausencia = ausencia.sort_values("_ordem").drop(columns=["_ordem"])

        fig_aus = px.bar(
            ausencia, x="POSTO_GRAD", y="Taxa (%)",
            color="Taxa (%)",
            color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
            text="Taxa (%)",
            labels={"POSTO_GRAD": "Posto/Graduação"},
            title="Percentual de ausência por posto",
        )
fig_aus.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_aus.update_layout(
            **DARK, height=350, coloraxis_showscale=False,
            xaxis=dict(**GRID), yaxis=dict(**GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_aus, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: POR QUADRO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📋 Por Quadro":
    st.markdown("""
    <h1 style="margin:0;font-size:2rem;">📋 Análise por Quadro</h1>
    <p style="margin:6px 0 12px;color:#94a3b8;">
      Comparativo de desempenho entre os diferentes quadros (QCOBM, QCPBM, QPBM, etc.)
    </p>
    """, unsafe_allow_html=True)
    st.divider()

    if len(df_presentes) == 0:
        st.warning("Nenhum dado disponível com os filtros atuais.")
    else:
        # Resumo por quadro
        st.markdown('<p class="section-title">📊 Resumo por Quadro</p>',
                    unsafe_allow_html=True)

        resumo_q = df_presentes.groupby("QUADRO").agg(
            Efetivo=("NOME", "count"),
            Media=("MEDIA_FINAL", "mean"),
            Mediana=("MEDIA_FINAL", "median"),
            Minimo=("MEDIA_FINAL", "min"),
            Maximo=("MEDIA_FINAL", "max"),
        ).reset_index()
        resumo_q.columns = ["Quadro", "Efetivo", "Média", "Mediana", "Mínimo", "Máximo"]
        for c in ["Média", "Mediana", "Mínimo", "Máximo"]:
            resumo_q[c] = resumo_q[c].round(2)
        resumo_q = resumo_q.sort_values("Média", ascending=False)
        st.dataframe(resumo_q, use_container_width=True, hide_index=True)

        # Média por quadro
        st.markdown('<p class="section-title">📈 Média por Quadro</p>',
                    unsafe_allow_html=True)

        df_q_media = df_presentes.groupby("QUADRO")["MEDIA_FINAL"].mean().reset_index()
        df_q_media = df_q_media.sort_values("MEDIA_FINAL", ascending=False)

        fig_q = px.bar(
            df_q_media, x="QUADRO", y="MEDIA_FINAL",
            color="MEDIA_FINAL",
            color_continuous_scale=["#ef4444", "#f59e0b", "#3b82f6", "#22c55e"],
            text="MEDIA_FINAL",
            labels={"QUADRO": "Quadro", "MEDIA_FINAL": "Média"},
            title="Média final por quadro",
        )
        fig_q.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_q.update_layout(
            **DARK, height=400, coloraxis_showscale=False,
            xaxis=dict(**GRID), yaxis=dict(range=[0, 11], **GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_q, use_container_width=True)

        # Box plot por quadro
        st.markdown('<p class="section-title">📦 Distribuição por Quadro</p>',
                    unsafe_allow_html=True)

        fig_box_q = px.box(
            df_presentes, x="QUADRO", y="MEDIA_FINAL",
            color="QUADRO",
            labels={"QUADRO": "Quadro", "MEDIA_FINAL": "Média Final"},
            title="Distribuição da média final por quadro",
        )
        fig_box_q.update_layout(
            **DARK, height=450, showlegend=False,
            xaxis=dict(**GRID), yaxis=dict(**GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_box_q, use_container_width=True)

        # Classificação por quadro (stacked bar)
        st.markdown('<p class="section-title">📊 Classificação por Quadro</p>',
                    unsafe_allow_html=True)

        class_q = df_presentes.groupby(
            ["QUADRO", "CLASSIFICACAO"]
        ).size().reset_index(name="Qtd")

        fig_stack_q = px.bar(
            class_q, x="QUADRO", y="Qtd", color="CLASSIFICACAO",
            color_discrete_map=COR_MAP, barmode="stack",
            labels={"QUADRO": "Quadro", "Qtd": "Quantidade"},
            title="Classificações por quadro",
        )
        fig_stack_q.update_layout(
            **DARK, height=400,
            xaxis=dict(**GRID), yaxis=dict(**GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_stack_q, use_container_width=True)

        # Radar por quadro
        st.markdown('<p class="section-title">🕸️ Radar Comparativo por Quadro</p>',
                    unsafe_allow_html=True)

        cores_q = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#a855f7"]
        fig_radar_q = go.Figure()
        for idx, quadro in enumerate(df_q_media["QUADRO"].tolist()):
            vals = df_presentes[df_presentes["QUADRO"] == quadro][colunas_nota].mean().tolist()
            fig_radar_q.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=cats_radar,
                name=quadro, line_color=cores_q[idx % len(cores_q)],
            ))
        fig_radar_q.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 10],
                                gridcolor="rgba(255,255,255,.12)",
                                tickfont_color="#94a3b8"),
                angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
            ),
            **DARK, height=450,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            title="Perfil de desempenho por quadro",
        )
        st.plotly_chart(fig_radar_q, use_container_width=True)

        # Desempenho por disciplina e quadro
        st.markdown('<p class="section-title">💪 Notas por Disciplina × Quadro</p>',
                    unsafe_allow_html=True)

        disc_data = []
        for q in df_presentes["QUADRO"].unique():
            for label, col in notas_map.items():
                media_val = df_presentes[df_presentes["QUADRO"] == q][col].mean()
                disc_data.append({"Quadro": q, "Disciplina": label, "Média": media_val})
        df_disc_q = pd.DataFrame(disc_data)

        fig_disc_q = px.bar(
            df_disc_q, x="Disciplina", y="Média", color="Quadro",
            barmode="group", text="Média",
            title="Média por disciplina e quadro",
        )
        fig_disc_q.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_disc_q.update_layout(
            **DARK, height=420,
            xaxis=dict(**GRID), yaxis=dict(range=[0, 11], **GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_disc_q, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: FICHA INDIVIDUAL
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "👤 Ficha Individual":
    st.markdown("""
    <h1 style="margin:0;font-size:2rem;">👤 Ficha Individual</h1>
    <p style="margin:6px 0 12px;color:#94a3b8;">
      Perfil detalhado de cada militar
    </p>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("**🔎 Selecionar Militar**")
        busca = st.text_input("Buscar por nome", placeholder="Digite parte do nome...")

        df_busca = df_all[df_all["PRESENTE"]].copy()
        lista_nomes = df_busca["NOME"].tolist()
        if busca:
            lista_nomes = [n for n in lista_nomes if busca.upper() in n]

        if lista_nomes:
            militar_sel = st.selectbox("Militar", lista_nomes)
        else:
            st.warning("Nenhum militar encontrado.")
            militar_sel = df_busca["NOME"].iloc[0] if len(df_busca) > 0 else None

    if militar_sel is None:
        st.warning("Nenhum militar disponível.")
    else:
        row = df_all[df_all["NOME"] == militar_sel].iloc[0]
        vals_ind = [float(row[c]) if pd.notna(row[c]) else 0.0 for c in colunas_nota]
        nome_curto = " ".join(str(militar_sel).split()[:2])
        media_ind = float(row["MEDIA_FINAL"]) if pd.notna(row["MEDIA_FINAL"]) else 0.0
        class_ind = row["CLASSIFICACAO"]
        posto_ind = row["POSTO_GRAD"]
        quadro_ind = row["QUADRO"]
        sexo_ind = row["sexo"]
        idade_ind = int(row["IDADE"]) if pd.notna(row["IDADE"]) else "N/A"

        # Comparações
        media_geral = df_all[df_all["PRESENTE"]]["MEDIA_FINAL"].mean()
        diff_geral = media_ind - media_geral

        # Média do mesmo posto
        media_posto = df_all[
            (df_all["PRESENTE"]) & (df_all["POSTO_GRAD"] == posto_ind)
        ]["MEDIA_FINAL"].mean()
        diff_posto = media_ind - media_posto

        # Ranking
        df_rank_calc = df_all[df_all["PRESENTE"] & df_all["MEDIA_FINAL"].notna()].copy()
        rank_pos = df_rank_calc["MEDIA_FINAL"].rank(ascending=False, method="min")
        posicao = int(rank_pos[df_rank_calc["NOME"] == militar_sel].values[0])
        total = len(df_rank_calc)

        pf_notas = {l: float(row[c]) for l, c in notas_map.items() if pd.notna(row[c])}
        pf_forte = max(pf_notas, key=pf_notas.get) if pf_notas else "—"
        pf_fraco = row["PONTO_FRACO"]

        badge_cor = {
            "Excelente":    ("#bbf7d0", "#166534", "rgba(34,197,94,.3)"),
            "Bom":          ("#bfdbfe", "#1e3a5f", "rgba(59,130,246,.3)"),
            "Regular":      ("#fde68a", "#78350f", "rgba(245,158,11,.3)"),
            "Insuficiente": ("#fecaca", "#7f1d1d", "rgba(239,68,68,.3)"),
        }.get(class_ind, ("#e7eefc", "#1e293b", "rgba(255,255,255,.1)"))

        sinal_g = "+" if diff_geral >= 0 else ""
        cor_g = "#22c55e" if diff_geral >= 0 else "#ef4444"
        sinal_p = "+" if diff_posto >= 0 else ""
        cor_p = "#22c55e" if diff_posto >= 0 else "#ef4444"

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(239,68,68,.15),rgba(59,130,246,.1));
                    border:1px solid rgba(239,68,68,.3);border-radius:16px;
                    padding:24px 28px;margin-bottom:20px;">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
            <div>
              <div style="font-size:1.8rem;font-weight:800;">🪖 {nome_curto}</div>
              <div style="color:#94a3b8;margin-top:4px;">
                {posto_ind} · {quadro_ind} · {sexo_ind} · {idade_ind} anos · CBMAM · 2026
              </div>
            </div>
            <div style="display:flex;gap:12px;flex-wrap:wrap;">
              <div style="background:{badge_cor[2]};border-radius:12px;padding:10px 20px;text-align:center;">
                <div style="font-size:.75rem;color:#94a3b8;">CLASSIFICAÇÃO</div>
                <div style="font-size:1.3rem;font-weight:800;color:{badge_cor[0]};">{class_ind}</div>
              </div>
              <div style="background:rgba(255,255,255,.05);border-radius:12px;padding:10px 20px;text-align:center;">
                <div style="font-size:.75rem;color:#94a3b8;">MÉDIA FINAL</div>
                <div style="font-size:1.3rem;font-weight:800;">{media_ind:.1f}</div>
              </div>
              <div style="background:rgba(255,255,255,.05);border-radius:12px;padding:10px 20px;text-align:center;">
                <div style="font-size:.75rem;color:#94a3b8;">RANKING</div>
                <div style="font-size:1.3rem;font-weight:800;">{posicao}° / {total}</div>
              </div>
              <div style="background:rgba(255,255,255,.05);border-radius:12px;padding:10px 20px;text-align:center;">
                <div style="font-size:.75rem;color:#94a3b8;">vs GERAL</div>
                <div style="font-size:1.3rem;font-weight:800;color:{cor_g};">{sinal_g}{diff_geral:.2f}</div>
              </div>
              <div style="background:rgba(255,255,255,.05);border-radius:12px;padding:10px 20px;text-align:center;">
                <div style="font-size:.75rem;color:#94a3b8;">vs {posto_ind}</div>
                <div style="font-size:1.3rem;font-weight:800;color:{cor_p};">{sinal_p}{diff_posto:.2f}</div>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Dados brutos do militar
        st.markdown('<p class="section-title">📝 Desempenho Bruto</p>',
                    unsafe_allow_html=True)
        raw_cols = st.columns(5)
        raw_data = [
            ("🏃 Corrida 12min", row["CORRIDA_RAW"], "metros"),
            ("💪 Abdominal", row["ABDOMINAL_RAW"], "reps"),
            ("🤸 Flexão", row["FLEXAO_RAW"], "reps"),
            ("🏊 Natação 50m", row["NATACAO_RAW"], ""),
            ("🔩 Barra", row["BARRA_RAW"], f"({row['BARRA_TIPO']})" if pd.notna(row.get("BARRA_TIPO")) else ""),
        ]
        for i, (label, val, unit) in enumerate(raw_data):
            with raw_cols[i]:
                display_val = str(val) if pd.notna(val) and str(val).strip() not in ("nan", "") else "—"
                st.markdown(f"""
                <div style="background:rgba(17,27,46,.8);border:1px solid rgba(255,255,255,.1);
                            border-radius:14px;padding:12px;text-align:center;">
                  <div style="font-size:.75rem;color:#94a3b8;">{label}</div>
                  <div style="font-size:1.5rem;font-weight:800;margin:4px 0;">{display_val}</div>
                  <div style="font-size:.7rem;color:#64748b;">{unit}</div>
                </div>
                """, unsafe_allow_html=True)

        # Radar e barras
        col_r, col_b2 = st.columns(2)

        med_geral_vals = [df_all[df_all["PRESENTE"]][c].mean() for c in colunas_nota]
        med_posto_vals = [
            df_all[(df_all["PRESENTE"]) & (df_all["POSTO_GRAD"] == posto_ind)][c].mean()
            for c in colunas_nota
        ]

        with col_r:
            st.markdown('<p class="section-title">🕸️ Radar de Atributos</p>',
                        unsafe_allow_html=True)

            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(
                r=[10] * len(cats_radar), theta=cats_radar, fill="toself", name="Máximo",
                line_color="rgba(255,255,255,.1)", fillcolor="rgba(255,255,255,.03)",
            ))
            fig_r.add_trace(go.Scatterpolar(
                r=med_geral_vals + [med_geral_vals[0]], theta=cats_radar,
                fill="toself", name="Média Geral",
                line_color="#f59e0b", fillcolor="rgba(245,158,11,.1)", line_dash="dot",
            ))
            fig_r.add_trace(go.Scatterpolar(
                r=med_posto_vals + [med_posto_vals[0]], theta=cats_radar,
                fill="toself", name=f"Média {posto_ind}",
                line_color="#a855f7", fillcolor="rgba(168,85,247,.1)", line_dash="dot",
            ))
            fig_r.add_trace(go.Scatterpolar(
                r=vals_ind + [vals_ind[0]], theta=cats_radar,
                fill="toself", name=nome_curto,
                line_color="#3b82f6", fillcolor="rgba(59,130,246,.2)",
            ))
            fig_r.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, range=[0, 10],
                                    gridcolor="rgba(255,255,255,.12)",
                                    tickfont_color="#94a3b8"),
                    angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
                ),
                **DARK,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25),
                height=440, margin=dict(t=30, b=70),
            )
            st.plotly_chart(fig_r, use_container_width=True)

        with col_b2:
            st.markdown('<p class="section-title">📊 Notas vs Referências</p>',
                        unsafe_allow_html=True)

            fig_b = go.Figure()
            fig_b.add_trace(go.Bar(
                name="Média Geral", x=labels_nota, y=med_geral_vals,
                marker_color="rgba(245,158,11,.5)",
                text=[f"{v:.1f}" for v in med_geral_vals], textposition="outside",
            ))
            fig_b.add_trace(go.Bar(
                name=nome_curto, x=labels_nota, y=vals_ind,
                marker_color=[
                    "#22c55e" if n >= m else "#ef4444"
                    for n, m in zip(vals_ind, med_geral_vals)
                ],
                text=[f"{v:.1f}" for v in vals_ind], textposition="outside",
            ))
            fig_b.update_layout(
                barmode="group", **DARK,
                yaxis=dict(range=[0, 12], **GRID), xaxis=dict(**GRID),
                legend=dict(orientation="h", yanchor="bottom", y=-0.25),
                height=440, margin=dict(t=30, b=70),
            )
            st.plotly_chart(fig_b, use_container_width=True)

        # Cards de notas
        st.markdown('<p class="section-title">🎯 Detalhamento por Disciplina</p>',
                    unsafe_allow_html=True)

        cols_disc = st.columns(5)
        for i, (label, col_n) in enumerate(zip(labels_nota, colunas_nota)):
            nota_v = float(row[col_n]) if pd.notna(row[col_n]) else 0.0
            med_v = df_all[df_all["PRESENTE"]][col_n].mean()
            delta_v = nota_v - med_v
            s = "+" if delta_v >= 0 else ""
            c_delta = "#22c55e" if delta_v >= 0 else "#ef4444"
            icone = "🟢" if nota_v >= med_v else "🔴"

            with cols_disc[i]:
                st.markdown(f"""
                <div style="background:rgba(17,27,46,.8);border:1px solid rgba(255,255,255,.1);
                            border-radius:14px;padding:16px;text-align:center;">
                  <div style="font-size:.8rem;color:#94a3b8;margin-bottom:8px;">{label}</div>
                  <div style="font-size:2rem;font-weight:800;">{nota_v:.1f}</div>
                  <div style="font-size:.8rem;color:{c_delta};margin-top:4px;">
                    {icone} {s}{delta_v:.2f} vs geral
                  </div>
                  <div style="background:rgba(255,255,255,.06);border-radius:6px;
                              margin-top:10px;height:6px;overflow:hidden;">
                    <div style="width:{nota_v * 10}%;height:100%;
                                background:{'#22c55e' if nota_v >= 9.0 else '#3b82f6' if nota_v >= 7.5 else '#f59e0b' if nota_v >= 6.0 else '#ef4444'};
                                border-radius:6px;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # Gauge
        st.markdown('<p class="section-title">🏁 Indicador de Média Final</p>',
                    unsafe_allow_html=True)

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=media_ind,
            delta={"reference": media_geral, "valueformat": ".2f",
                   "increasing": {"color": "#22c55e"},
                   "decreasing": {"color": "#ef4444"}},
            title={"text": f"Média Final · {nome_curto}<br>"
                   f"<span style='font-size:.8rem;color:#94a3b8'>"
                   f"Ref: média geral ({media_geral:.2f})</span>"},
            gauge={
                "axis": {"range": [0, 10], "tickcolor": "#94a3b8"},
                "bar": {"color": COR_MAP.get(class_ind, "#3b82f6")},
                "bgcolor": "rgba(0,0,0,0)",
                "bordercolor": "rgba(255,255,255,.1)",
                "steps": [
                    {"range": [0, 6.0], "color": "rgba(239,68,68,.15)"},
                    {"range": [6.0, 7.5], "color": "rgba(245,158,11,.15)"},
                    {"range": [7.5, 9.0], "color": "rgba(59,130,246,.15)"},
                    {"range": [9.0, 10], "color": "rgba(34,197,94,.15)"},
                ],
                "threshold": {
                    "line": {"color": "#f59e0b", "width": 3},
                    "thickness": 0.8,
                    "value": media_geral,
                },
            },
            number={"font": {"color": "#e7eefc", "size": 56}},
        ))
        fig_gauge.update_layout(
            **DARK, height=320, margin=dict(t=60, b=20, l=40, r=40),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Resumo
        st.markdown(f"""
        <div style="background:rgba(17,27,46,.8);border:1px solid rgba(255,255,255,.1);
                    border-radius:14px;padding:20px;margin-top:10px;line-height:2;">
          <b>🪖 Posto/Graduação:</b> {posto_ind} · {quadro_ind}<br>
          <b>🚻 Sexo:</b> {sexo_ind} · <b>🎂 Idade:</b> {idade_ind} anos<br>
          <b>🟢 Ponto forte:</b> {pf_forte} ({pf_notas.get(pf_forte, 0):.1f})<br>
          <b>🔴 Ponto fraco:</b> {pf_fraco} ({pf_notas.get(pf_fraco, 0):.1f})<br>
          <b>📍 Ranking:</b> {posicao}° de {total} avaliados<br>
          <b>📈 vs Média geral ({media_geral:.2f}):</b>
          <span style="color:{cor_g};font-weight:700;">{sinal_g}{diff_geral:.2f}</span><br>
          <b>📈 vs Média {posto_ind} ({media_posto:.2f}):</b>
          <span style="color:{cor_p};font-weight:700;">{sinal_p}{diff_posto:.2f}</span>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: ESTATÍSTICAS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📈 Estatísticas":
    st.markdown("""
    <h1 style="margin:0;font-size:2rem;">📈 Análise Estatística</h1>
    <p style="margin:6px 0 12px;color:#94a3b8;">
      Boxplots, distribuições, correlações e percentis do TAF
    </p>
    """, unsafe_allow_html=True)
    st.divider()

    if len(df_presentes) == 0:
        st.warning("Nenhum dado disponível.")
    else:
        # Box plots por disciplina
        st.markdown('<p class="section-title">📦 Box Plot — Notas por Disciplina</p>',
                    unsafe_allow_html=True)

        box_data = []
        for label, col in notas_map.items():
            for val in df_presentes[col].dropna():
                box_data.append({"Disciplina": label, "Nota": val})
        df_box = pd.DataFrame(box_data)

        fig_box = px.box(
            df_box, x="Disciplina", y="Nota", color="Disciplina",
            title="Distribuição de notas por disciplina",
        )
        fig_box.update_layout(
            **DARK, height=450, showlegend=False,
            xaxis=dict(**GRID), yaxis=dict(range=[0, 11], **GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_box, use_container_width=True)

        # Histogramas sobrepostos
        st.markdown('<p class="section-title">📉 Distribuição de Notas por Disciplina</p>',
                    unsafe_allow_html=True)

        fig_hist_all = go.Figure()
        cores = ["#ef4444", "#f59e0b", "#3b82f6", "#22c55e", "#a855f7"]
        for i, (label, col) in enumerate(notas_map.items()):
            vals = df_presentes[col].dropna()
            fig_hist_all.add_trace(go.Histogram(
                x=vals, name=label, opacity=0.6,
                marker_color=cores[i], nbinsx=12,
            ))
        fig_hist_all.update_layout(
            **DARK, height=400, barmode="overlay",
            xaxis=dict(title="Nota", **GRID),
            yaxis=dict(title="Frequência", **GRID),
            title="Sobreposição de distribuições",
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_hist_all, use_container_width=True)

        # Correlação corrida x média
        st.markdown('<p class="section-title">🏃 Correlação: Corrida × Média Final</p>',
                    unsafe_allow_html=True)

        df_corr = df_presentes[df_presentes["CORRIDA"].notna()].copy()
        fig_scatter = px.scatter(
            df_corr, x="CORRIDA", y="MEDIA_FINAL",
            color="CLASSIFICACAO", color_discrete_map=COR_MAP,
            size="MEDIA_FINAL", hover_name="NOME",
            trendline="ols", trendline_color_override="#ffffff",
            labels={"CORRIDA": "Corrida 12min (metros)", "MEDIA_FINAL": "Média Final"},
            title="Militares com maior distância na corrida têm média mais alta?",
        )
        fig_scatter.update_layout(
            **DARK, height=420,
            yaxis=dict(**GRID), xaxis=dict(**GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        # Tabela de percentis
        st.markdown('<p class="section-title">📊 Tabela de Percentis</p>',
                    unsafe_allow_html=True)

        percentis = [10, 25, 50, 75, 90]
        perc_data = {"Percentil": [f"P{p}" for p in percentis]}
        for label, col in notas_map.items():
            vals = df_presentes[col].dropna()
            perc_data[label] = [round(np.percentile(vals, p), 2) if len(vals) > 0 else 0
                                for p in percentis]
        perc_data["Média Final"] = [
            round(np.percentile(df_presentes["MEDIA_FINAL"].dropna(), p), 2)
            for p in percentis
        ]
        st.dataframe(pd.DataFrame(perc_data), use_container_width=True, hide_index=True)

        # Estatísticas descritivas
        st.markdown('<p class="section-title">📋 Estatísticas Descritivas</p>',
                    unsafe_allow_html=True)

        desc_cols = list(notas_map.values()) + ["MEDIA_FINAL"]
        desc_labels = list(notas_map.keys()) + ["Média Final"]
        desc = df_presentes[desc_cols].describe().T
        desc.index = desc_labels
        desc = desc[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]]
        desc.columns = ["N", "Média", "Desvio", "Mín", "P25", "Mediana", "P75", "Máx"]
        desc = desc.round(2)
        st.dataframe(desc, use_container_width=True)

        # Top 10 e Bottom 10
        st.markdown('<p class="section-title">🏆 Top 10 e Bottom 10</p>',
                    unsafe_allow_html=True)

        col_t, col_bt = st.columns(2)
        with col_t:
            st.markdown("**🥇 Top 10 — Maiores Médias**")
            top10 = df_presentes.nlargest(10, "MEDIA_FINAL")[
                ["NOME", "POSTO_GRAD", "QUADRO", "sexo", "IDADE", "MEDIA_FINAL", "CLASSIFICACAO"]
            ].reset_index(drop=True)
            top10.index += 1
            st.dataframe(top10, use_container_width=True)

        with col_bt:
            st.markdown("**⚠️ Bottom 10 — Menores Médias**")
            bot10 = df_presentes.nsmallest(10, "MEDIA_FINAL")[
                ["NOME", "POSTO_GRAD", "QUADRO", "sexo", "IDADE", "MEDIA_FINAL", "CLASSIFICACAO"]
            ].reset_index(drop=True)
            bot10.index += 1
            st.dataframe(bot10, use_container_width=True)

        # Valores brutos — desempenho real
        st.markdown('<p class="section-title">🔢 Desempenho Bruto (Valores Reais)</p>',
                    unsafe_allow_html=True)

        raw_stats = pd.DataFrame({
            "Exercício": ["Corrida 12min (m)", "Abdominal (reps)", "Flexão (reps)",
                          "Natação 50m (seg)", "Barra (valor)"],
            "Média": [
                df_presentes["CORRIDA"].mean(),
                df_presentes["ABDOMINAL"].mean(),
                df_presentes["FLEXAO"].mean(),
                df_presentes["NATACAO_SEG"].mean(),
                df_presentes["BARRA_VALOR"].mean(),
            ],
            "Mediana": [
                df_presentes["CORRIDA"].median(),
                df_presentes["ABDOMINAL"].median(),
                df_presentes["FLEXAO"].median(),
                df_presentes["NATACAO_SEG"].median(),
                df_presentes["BARRA_VALOR"].median(),
            ],
            "Mínimo": [
                df_presentes["CORRIDA"].min(),
                df_presentes["ABDOMINAL"].min(),
                df_presentes["FLEXAO"].min(),
                df_presentes["NATACAO_SEG"].min(),
                df_presentes["BARRA_VALOR"].min(),
            ],
            "Máximo": [
                df_presentes["CORRIDA"].max(),
                df_presentes["ABDOMINAL"].max(),
                df_presentes["FLEXAO"].max(),
                df_presentes["NATACAO_SEG"].max(),
                df_presentes["BARRA_VALOR"].max(),
            ],
        }).round(1)
        st.dataframe(raw_stats, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: TAF ADAPTADO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "♿ TAF Adaptado":
    st.markdown("""
    <h1 style="margin:0;font-size:2rem;">♿ TAF Adaptado</h1>
    <p style="margin:6px 0 12px;color:#94a3b8;">
      Dados dos militares que realizaram o TAF na modalidade adaptada
    </p>
    """, unsafe_allow_html=True)
    st.divider()

    if len(df_adaptado) == 0:
        st.warning("Nenhum dado de TAF Adaptado encontrado.")
    else:
        # KPIs
        total_adapt = len(df_adaptado)
        presentes_adapt = int(df_adaptado["PRESENTE"].sum())
        ausentes_adapt = total_adapt - presentes_adapt

        k1, k2, k3 = st.columns(3)
        k1.metric("👥 Total", total_adapt)
        k2.metric("✅ Presentes", presentes_adapt)
        k3.metric("❌ Ausentes", ausentes_adapt)

        st.divider()

        # Por posto
        st.markdown('<p class="section-title">🪖 Efetivo por Posto/Graduação</p>',
                    unsafe_allow_html=True)

        adapt_posto = df_adaptado.groupby("POSTO_GRAD").size().reset_index(name="Quantidade")
        adapt_posto["_ordem"] = adapt_posto["POSTO_GRAD"].apply(ordem_posto)
        adapt_posto = adapt_posto.sort_values("_ordem").drop(columns=["_ordem"])

        fig_adapt = px.bar(
            adapt_posto, x="POSTO_GRAD", y="Quantidade",
            color="Quantidade",
            color_continuous_scale=["#3b82f6", "#22c55e"],
            text="Quantidade",
            labels={"POSTO_GRAD": "Posto/Graduação"},
            title="Militares no TAF Adaptado por posto",
        )
        fig_adapt.update_traces(textposition="outside")
        fig_adapt.update_layout(
            **DARK, height=350, coloraxis_showscale=False,
            xaxis=dict(**GRID), yaxis=dict(**GRID),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_adapt, use_container_width=True)

        # Tabela de dados
        st.markdown('<p class="section-title">📋 Dados Completos — TAF Adaptado</p>',
                    unsafe_allow_html=True)

        display_cols = [c for c in df_adaptado.columns if c not in ["PRESENTE", "_ordem"]]
        df_adapt_display = df_adaptado[display_cols].copy()
        df_adapt_display = df_adapt_display.fillna("—")

        # Limpar valores "nan"
        for col in df_adapt_display.columns:
            df_adapt_display[col] = df_adapt_display[col].astype(str).replace("nan", "—")

        st.dataframe(df_adapt_display, use_container_width=True, height=500)

        # Exercícios realizados
        st.markdown('<p class="section-title">📊 Exercícios Realizados</p>',
                    unsafe_allow_html=True)

        exercicios_adapt = ["CAMINHADA", "ABDOMINAL", "FLEXAO", "PRANCHA", "NATACAO",
                            "BARRA_EST", "BARRA_DIN", "CORRIDA", "PUXADOR_FRONTAL",
                            "FLUTUACAO", "SUPINO", "COOPER"]
        ex_count = {}
        for ex in exercicios_adapt:
            if ex in df_adaptado.columns:
                count = df_adaptado[ex].dropna().apply(
                    lambda x: str(x).strip() not in ("", "nan", "NÃO COMPARECEU", "NÃO")
                ).sum()
                ex_count[ex] = count

        ex_df = pd.DataFrame({
            "Exercício": list(ex_count.keys()),
            "Realizaram": list(ex_count.values()),
        }).sort_values("Realizaram", ascending=False)
        ex_df = ex_df[ex_df["Realizaram"] > 0]

        if len(ex_df) > 0:
            fig_ex = px.bar(
                ex_df, x="Exercício", y="Realizaram",
                color="Realizaram",
                color_continuous_scale=["#f59e0b", "#22c55e"],
                text="Realizaram",
                title="Quantidade de militares por exercício (TAF Adaptado)",
            )
            fig_ex.update_traces(textposition="outside")
            fig_ex.update_layout(
                **DARK, height=400, coloraxis_showscale=False,
                xaxis=dict(**GRID, tickangle=-45),
                yaxis=dict(**GRID),
                margin=dict(t=50, b=20),
            )
            st.plotly_chart(fig_ex, use_container_width=True)

        st.info(
            "ℹ️ O TAF Adaptado avalia militares com necessidades especiais ou "
            "restrições médicas, utilizando exercícios alternativos conforme "
            "aptidão individual. Cada militar realiza um conjunto diferente de provas."
        )
