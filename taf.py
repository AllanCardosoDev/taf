import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path

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
  .foto-pelotao {
    border-radius: 16px;
    border: 2px solid rgba(239,68,68,.5);
    box-shadow: 0 0 30px rgba(239,68,68,.25);
    width: 100%;
    object-fit: cover;
  }
  .card-militar {
    background: rgba(17,27,46,.9);
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 14px;
    padding: 20px;
    margin-top: 10px;
  }
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Dados ─────────────────────────────────────────────────────────────────────
@st.cache_data
def carregar_dados():
    df_raw = pd.read_excel("table.xlsx", engine="openpyxl", header=None)

    primeira = str(df_raw.iloc[0, 0]).strip()
    if not primeira.lstrip("-").replace(",", "").replace(".", "").isdigit():
        df_raw = df_raw.iloc[1:].reset_index(drop=True)

    nomes_col = [
        "ORD", "NOME",
        "CORRIDA_12MIN", "NOTA_CORRIDA",
        "ABDOMINAL",     "NOTA_ABDOMINAL",
        "FLEXAO_BRACOS", "NOTA_FLEXAO",
        "NATACAO_50M",   "NOTA_NATACAO",
        "BARRA",         "NOTA_BARRA",
        "MEDIA_FINAL",
    ]
    df = df_raw.iloc[:, :13].copy()
    df.columns = nomes_col

    colunas_num = [
        "CORRIDA_12MIN", "NOTA_CORRIDA",
        "ABDOMINAL",     "NOTA_ABDOMINAL",
        "FLEXAO_BRACOS", "NOTA_FLEXAO",
        "NOTA_NATACAO",  "NOTA_BARRA",
        "MEDIA_FINAL",
    ]
    for col in colunas_num:
        df[col] = (
            df[col].astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["MEDIA_FINAL"].notna() & (df["MEDIA_FINAL"] > 0)].reset_index(drop=True)
    df["NOME"] = df["NOME"].astype(str).str.strip().str.upper()

    def classificar(m):
        if m >= 9.5:    return "Excelente"
        elif m >= 8.5:  return "Bom"
        elif m >= 7.0:  return "Regular"
        else:           return "Atenção"

    df["CLASSIFICACAO"] = df["MEDIA_FINAL"].apply(classificar)

    notas = {
        "Corrida 12min":    "NOTA_CORRIDA",
        "Abdominal":        "NOTA_ABDOMINAL",
        "Flexão de Braços": "NOTA_FLEXAO",
        "Natação 50m":      "NOTA_NATACAO",
        "Barra":            "NOTA_BARRA",
    }

    def ponto_fraco(row):
        vals = {k: float(row[v]) for k, v in notas.items() if pd.notna(row[v])}
        return min(vals, key=vals.get) if vals else "—"

    df["PONTO_FRACO"] = df.apply(ponto_fraco, axis=1)
    return df, notas


df, notas = carregar_dados()
colunas_nota = list(notas.values())
labels_nota  = list(notas.keys())
cor_map = {
    "Excelente": "#22c55e",
    "Bom":       "#3b82f6",
    "Regular":   "#f59e0b",
    "Atenção":   "#ef4444",
}
cats = labels_nota + [labels_nota[0]]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/"
        "Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Amazonas.svg/"
        "200px-Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Amazonas.svg.png",
        width=90,
    )
    st.markdown("## CBMAM · TAF Dashboard")
    st.markdown("**3º Pelotão · Japurá**")
    st.divider()

    classificacoes = ["Todos"] + sorted(df["CLASSIFICACAO"].unique().tolist())
    filtro_class = st.selectbox("Filtrar por classificação", classificacoes)

    nota_minima = st.slider(
        "Média final mínima", 0.0, 10.0,
        float(df["MEDIA_FINAL"].min()), 0.1,
    )

    st.divider()
    st.markdown(
        "<small>Desenvolvido para análise de desempenho físico militar.<br>"
        "CBMAM · BM-6/EMG · 2026</small>",
        unsafe_allow_html=True,
    )


# ── Filtro ────────────────────────────────────────────────────────────────────
df_f = df.copy()
if filtro_class != "Todos":
    df_f = df_f[df_f["CLASSIFICACAO"] == filtro_class]
df_f = df_f[df_f["MEDIA_FINAL"] >= nota_minima]


# ── Cabeçalho com foto do pelotão ─────────────────────────────────────────────
col_header, col_foto = st.columns([2, 1])

with col_header:
    st.markdown("""
    <div style="margin-bottom:6px;">
      <h1 style="margin:0;font-size:2rem;">🔥 Avaliação Prática · TAF</h1>
      <p style="margin:6px 0 0;color:#94a3b8;font-size:1rem;">
        Corpo de Bombeiros Militar do Amazonas &nbsp;·&nbsp;
        3º Pelotão · Japurá &nbsp;·&nbsp; 2026
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    > **Por que analisar dados do TAF?**
    > O acompanhamento sistemático do desempenho físico dos militares permite identificar
    > pontos críticos de melhoria individual e coletiva, orientar treinamentos direcionados,
    > prevenir afastamentos por lesão e elevar o nível operacional da corporação.
    > Dados bem analisados salvam vidas — dentro e fora do quartel.
    """)

with col_foto:
    foto_path = Path("japura.enc")
    if foto_path.exists():
        st.markdown('<div style="margin-top:10px;">', unsafe_allow_html=True)
        st.image(
            str(foto_path),
            caption="3º Pelotão · Japurá · CBMAM",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

st.divider()


# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📊 Visão Geral do Pelotão</p>', unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)

media_geral = df_f["MEDIA_FINAL"].mean()
melhor      = df_f.loc[df_f["MEDIA_FINAL"].idxmax()]
pior        = df_f.loc[df_f["MEDIA_FINAL"].idxmin()]
excelentes  = len(df_f[df_f["CLASSIFICACAO"] == "Excelente"])
atencao     = len(df_f[df_f["CLASSIFICACAO"] == "Atenção"])

k1.metric("👥 Avaliados",          len(df_f))
k2.metric("📈 Média geral",        f"{media_geral:.2f}")
k3.metric("🥇 Maior média",        f"{melhor['MEDIA_FINAL']:.1f}", melhor["NOME"].split()[0])
k4.metric("⚠️ Menor média",        f"{pior['MEDIA_FINAL']:.1f}",   pior["NOME"].split()[0])
k5.metric("✅ Excelentes (≥ 9,5)", excelentes)
k6.metric("🚨 Atenção (< 7,0)",    atencao)

st.divider()


# ── Ranking ───────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🏆 Ranking de Desempenho — Média Final</p>', unsafe_allow_html=True)

df_rank = df_f.sort_values("MEDIA_FINAL", ascending=True).copy()
df_rank["NOME_CURTO"] = df_rank["NOME"].apply(lambda x: " ".join(str(x).split()[:2]))

fig_rank = px.bar(
    df_rank, x="MEDIA_FINAL", y="NOME_CURTO", orientation="h",
    color="CLASSIFICACAO", color_discrete_map=cor_map,
    text="MEDIA_FINAL",
    hover_data={"NOME": True, "MEDIA_FINAL": True, "CLASSIFICACAO": True},
    labels={"MEDIA_FINAL": "Média Final", "NOME_CURTO": ""},
)
fig_rank.update_traces(texttemplate="%{text:.1f}", textposition="outside")
fig_rank.update_layout(
    height=max(500, len(df_rank) * 22),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc", legend_title_text="Classificação",
    xaxis=dict(range=[0, 11], gridcolor="rgba(255,255,255,.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    margin=dict(l=10, r=60, t=20, b=20),
)
st.plotly_chart(fig_rank, use_container_width=True)


# ── Distribuição ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📉 Distribuição de Desempenho</p>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)

with col_a:
    contagem = df_f["CLASSIFICACAO"].value_counts().reset_index()
    contagem.columns = ["Classificação", "Quantidade"]
    ordem = ["Excelente", "Bom", "Regular", "Atenção"]
    contagem["Classificação"] = pd.Categorical(
        contagem["Classificação"], categories=ordem, ordered=True
    )
    contagem = contagem.sort_values("Classificação")
    fig_pie = px.pie(
        contagem, names="Classificação", values="Quantidade",
        color="Classificação", color_discrete_map=cor_map,
        hole=0.52, title="Proporção por classificação",
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font_color="#e7eefc",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=50, b=10),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    fig_hist = px.histogram(
        df_f, x="MEDIA_FINAL", nbins=15,
        color_discrete_sequence=["#3b82f6"],
        title="Histograma de médias finais",
        labels={"MEDIA_FINAL": "Média Final", "count": "Frequência"},
    )
    fig_hist.add_vline(
        x=media_geral, line_dash="dash", line_color="#ef4444",
        annotation_text=f"Média: {media_geral:.2f}",
        annotation_font_color="#ef4444",
    )
    fig_hist.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e7eefc", margin=dict(t=50, b=10),
        yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
        xaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    )
    st.plotly_chart(fig_hist, use_container_width=True)


# ── Média por disciplina ──────────────────────────────────────────────────────
st.markdown('<p class="section-title">💪 Desempenho Médio por Disciplina</p>', unsafe_allow_html=True)

medias_disc = {
    label: df_f[col].mean()
    for label, col in zip(labels_nota, colunas_nota)
}
df_disc = pd.DataFrame({
    "Disciplina": list(medias_disc.keys()),
    "Média":      list(medias_disc.values()),
}).sort_values("Média")

fig_disc = px.bar(
    df_disc, x="Média", y="Disciplina", orientation="h", text="Média",
    color="Disciplina",
    color_discrete_sequence=[
        "#ef4444" if v < 9.0 else "#22c55e" for v in df_disc["Média"]
    ],
    title="Onde o pelotão se sai melhor e pior",
)
fig_disc.update_traces(texttemplate="%{text:.2f}", textposition="outside", showlegend=False)
fig_disc.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc",
    xaxis=dict(range=[0, 11], gridcolor="rgba(255,255,255,.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    margin=dict(l=10, r=70, t=50, b=20), height=320,
)
st.plotly_chart(fig_disc, use_container_width=True)

disciplina_mais_fraca = df_disc.iloc[0]["Disciplina"]
nota_mais_fraca       = df_disc.iloc[0]["Média"]
disciplina_mais_forte = df_disc.iloc[-1]["Disciplina"]

st.info(
    f"**📌 Insight automático:** A disciplina com menor média coletiva é "
    f"**{disciplina_mais_fraca}** ({nota_mais_fraca:.2f}), indicando necessidade "
    f"de atenção no treinamento específico dessa modalidade. "
    f"O ponto forte do pelotão é **{disciplina_mais_forte}**."
)


# ── Radar Top 5 vs Bottom 5 ───────────────────────────────────────────────────
st.markdown('<p class="section-title">🕸️ Radar de Perfil — Top 5 vs Bottom 5</p>', unsafe_allow_html=True)

top5    = df_f.nlargest(5,  "MEDIA_FINAL")[colunas_nota].mean().tolist()
bottom5 = df_f.nsmallest(5, "MEDIA_FINAL")[colunas_nota].mean().tolist()

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=top5 + [top5[0]], theta=cats, fill="toself", name="Top 5",
    line_color="#22c55e", fillcolor="rgba(34,197,94,.15)",
))
fig_radar.add_trace(go.Scatterpolar(
    r=bottom5 + [bottom5[0]], theta=cats, fill="toself", name="Bottom 5",
    line_color="#ef4444", fillcolor="rgba(239,68,68,.15)",
))
fig_radar.update_layout(
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(visible=True, range=[0, 10],
                        gridcolor="rgba(255,255,255,.12)", tickfont_color="#94a3b8"),
        angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
    ),
    paper_bgcolor="rgba(0,0,0,0)", font_color="#e7eefc",
    legend=dict(orientation="h", yanchor="bottom", y=-0.15),
    height=420,
    title="Comparativo de perfil físico entre os extremos do pelotão — Japurá",
)
st.plotly_chart(fig_radar, use_container_width=True)


# ── Mapa de calor ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🌡️ Mapa de Calor — Notas individuais por disciplina</p>',
            unsafe_allow_html=True)

df_heat = df_f[["NOME"] + colunas_nota].copy()
df_heat["NOME_CURTO"] = df_heat["NOME"].apply(lambda x: " ".join(str(x).split()[:2]))
df_heat = df_heat.sort_values("NOTA_CORRIDA", ascending=False)

z_vals = df_heat[colunas_nota].values.tolist()
nomes  = df_heat["NOME_CURTO"].tolist()

fig_heat = go.Figure(go.Heatmap(
    z=z_vals, x=labels_nota, y=nomes,
    colorscale=[
        [0.0,  "#ef4444"],
        [0.5,  "#f59e0b"],
        [0.75, "#3b82f6"],
        [1.0,  "#22c55e"],
    ],
    zmin=0, zmax=10,
    text=[[f"{v:.1f}" if pd.notna(v) else "—" for v in row] for row in z_vals],
    texttemplate="%{text}",
    hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>",
    colorbar=dict(title="Nota", tickfont_color="#e7eefc", title_font_color="#e7eefc"),
))
fig_heat.update_layout(
    height=max(500, len(df_heat) * 22),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc",
    margin=dict(l=10, r=10, t=20, b=20),
    xaxis=dict(side="top"),
)
st.plotly_chart(fig_heat, use_container_width=True)


# ── Pontos fracos ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🔍 Disciplinas com Mais Pontos Fracos</p>',
            unsafe_allow_html=True)

pontos_fracos = df_f["PONTO_FRACO"].value_counts().reset_index()
pontos_fracos.columns = ["Disciplina", "Quantidade"]

fig_pf = px.bar(
    pontos_fracos, x="Disciplina", y="Quantidade",
    color="Quantidade",
    color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
    text="Quantidade",
    title="Disciplina onde cada militar tem sua pior nota",
    labels={"Quantidade": "Nº de militares", "Disciplina": ""},
)
fig_pf.update_traces(textposition="outside")
fig_pf.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc", coloraxis_showscale=False,
    yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    xaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    margin=dict(t=50, b=20), height=350,
)
st.plotly_chart(fig_pf, use_container_width=True)

disciplina_critica = pontos_fracos.iloc[0]["Disciplina"]
qtd_critica        = pontos_fracos.iloc[0]["Quantidade"]
st.warning(
    f"⚠️ **{qtd_critica} militares** têm seu pior desempenho em "
    f"**{disciplina_critica}**. Recomenda-se treino focado nessa modalidade."
)


# ── Correlação ────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🏃 Correlação: Corrida 12min × Média Final</p>',
            unsafe_allow_html=True)

fig_scatter = px.scatter(
    df_f, x="CORRIDA_12MIN", y="MEDIA_FINAL",
    color="CLASSIFICACAO", color_discrete_map=cor_map,
    size="MEDIA_FINAL", hover_name="NOME",
    trendline="ols", trendline_color_override="#ffffff",
    labels={
        "CORRIDA_12MIN": "Metros percorridos (12 min)",
        "MEDIA_FINAL":   "Média Final",
    },
    title="Militares com maior distância na corrida tendem a ter média final mais alta?",
)
fig_scatter.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc",
    yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    xaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    margin=dict(t=50, b=20), height=420,
)
st.plotly_chart(fig_scatter, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ── FICHA INDIVIDUAL DO MILITAR ───────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown('<p class="section-title">🪖 Análise Individual por Militar</p>',
            unsafe_allow_html=True)

busca = st.text_input("🔎 Buscar militar pelo nome", key="busca_individual")
df_busca = df_f.copy()
if busca:
    df_busca = df_busca[df_busca["NOME"].str.upper().str.contains(busca.upper(), na=False)]

if df_busca.empty:
    st.warning("Nenhum militar encontrado com esse filtro.")
    st.stop()

militar_sel = st.selectbox(
    "Selecione o militar",
    df_busca["NOME"].tolist(),
    key="militar_individual",
)

row = df_f[df_f["NOME"] == militar_sel].iloc[0]
vals_ind   = [float(row[c]) if pd.notna(row[c]) else 0.0 for c in colunas_nota]
nome_curto = " ".join(str(militar_sel).split()[:2])

pf_notas  = {l: float(row[c]) for l, c in zip(labels_nota, colunas_nota) if pd.notna(row[c])}
pf_forte  = max(pf_notas, key=pf_notas.get) if pf_notas else "—"
pf_fraco  = row["PONTO_FRACO"]
media_ind = float(row["MEDIA_FINAL"])
class_ind = row["CLASSIFICACAO"]

# Cor do badge de classificação
badge_cor = {
    "Excelente": ("#bbf7d0", "rgba(34,197,94,.25)"),
    "Bom":       ("#bfdbfe", "rgba(59,130,246,.25)"),
    "Regular":   ("#fde68a", "rgba(245,158,11,.25)"),
    "Atenção":   ("#fecaca", "rgba(239,68,68,.25)"),
}.get(class_ind, ("#e7eefc", "rgba(255,255,255,.1)"))

# Diferença em relação à média do pelotão
diff_media = media_ind - media_geral
sinal = "+" if diff_media >= 0 else ""
cor_diff = "#22c55e" if diff_media >= 0 else "#ef4444"

# Posição no ranking
rank_pos = df_f["MEDIA_FINAL"].rank(ascending=False, method="min")
posicao  = int(rank_pos[df_f["NOME"] == militar_sel].values[0])

# ── Layout da ficha ───────────────────────────────────────────────────────────
col_radar, col_bar, col_info = st.columns([1.2, 1.2, 0.9])

# Radar individual
with col_radar:
    fig_ind = go.Figure()
    fig_ind.add_trace(go.Scatterpolar(
        r=[10] * len(cats), theta=cats,
        fill="toself", name="Máximo",
        line_color="rgba(255,255,255,.12)",
        fillcolor="rgba(255,255,255,.04)",
    ))
    # Média do pelotão como referência
    media_pel = [df_f[c].mean() for c in colunas_nota]
    fig_ind.add_trace(go.Scatterpolar(
        r=media_pel + [media_pel[0]], theta=cats,
        fill="toself", name="Média Pelotão",
        line_color="#f59e0b",
        fillcolor="rgba(245,158,11,.1)",
        line_dash="dot",
    ))
    fig_ind.add_trace(go.Scatterpolar(
        r=vals_ind + [vals_ind[0]], theta=cats,
        fill="toself", name=nome_curto,
        line_color="#3b82f6",
        fillcolor="rgba(59,130,246,.2)",
    ))
    fig_ind.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 10],
                            gridcolor="rgba(255,255,255,.12)",
                            tickfont_color="#94a3b8"),
            angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
        ),
        paper_bgcolor="rgba(0,0,0,0)", font_color="#e7eefc",
        title=f"Radar · {nome_curto}",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        height=420,
        margin=dict(t=60, b=60),
    )
    st.plotly_chart(fig_ind, use_container_width=True)

# Barras por disciplina
with col_bar:
    df_bar_ind = pd.DataFrame({
        "Disciplina": labels_nota,
        "Nota":       vals_ind,
        "Média Pelotão": [df_f[c].mean() for c in colunas_nota],
    })

    fig_bar_ind = go.Figure()
    fig_bar_ind.add_trace(go.Bar(
        name="Média Pelotão",
        x=df_bar_ind["Disciplina"],
        y=df_bar_ind["Média Pelotão"],
        marker_color="rgba(245,158,11,.5)",
        text=[f"{v:.1f}" for v in df_bar_ind["Média Pelotão"]],
        textposition="outside",
    ))
    fig_bar_ind.add_trace(go.Bar(
        name=nome_curto,
        x=df_bar_ind["Disciplina"],
        y=df_bar_ind["Nota"],
        marker_color=[
            "#22c55e" if n >= m else "#ef4444"
            for n, m in zip(df_bar_ind["Nota"], df_bar_ind["Média Pelotão"])
        ],
        text=[f"{v:.1f}" for v in df_bar_ind["Nota"]],
        textposition="outside",
    ))
    fig_bar_ind.update_layout(
        barmode="group",
        title=f"Notas vs Média do Pelotão",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e7eefc",
        yaxis=dict(range=[0, 11.5], gridcolor="rgba(255,255,255,.06)"),
        xaxis=dict(gridcolor="rgba(255,255,255,.06)"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        margin=dict(t=50, b=60), height=420,
    )
    st.plotly_chart(fig_bar_ind, use_container_width=True)

# Card de informações
with col_info:
    st.markdown(f"""
    <div class="card-militar">
      <div style="font-size:1.1rem;font-weight:700;margin-bottom:14px;
                  border-bottom:1px solid rgba(255,255,255,.1);padding-bottom:10px;">
        {nome_curto}
      </div>

      <div style="margin-bottom:12px;">
        <div style="color:#94a3b8;font-size:.8rem;">CLASSIFICAÇÃO</div>
        <div style="background:{badge_cor[1]};color:{badge_cor[0]};
                    border-radius:8px;padding:6px 12px;margin-top:4px;
                    font-weight:700;font-size:1rem;display:inline-block;">
          {class_ind}
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
        <div style="background:rgba(255,255,255,.05);border-radius:10px;padding:10px;text-align:center;">
          <div style="color:#94a3b8;font-size:.75rem;">MÉDIA FINAL</div>
          <div style="font-size:1.6rem;font-weight:800;">{media_ind:.1f}</div>
        </div>
        <div style="background:rgba(255,255,255,.05);border-radius:10px;padding:10px;text-align:center;">
          <div style="color:#94a3b8;font-size:.75rem;">RANKING</div>
          <div style="font-size:1.6rem;font-weight:800;">{posicao}º</div>
        </div>
      </div>

      <div style="background:rgba(255,255,255,.05);border-radius:10px;
                  padding:10px;text-align:center;margin-bottom:14px;">
        <div style="color:#94a3b8;font-size:.75rem;">vs MÉDIA DO PELOTÃO</div>
        <div style="font-size:1.3rem;font-weight:700;color:{cor_diff};">
          {sinal}{diff_media:.2f} pts
        </div>
      </div>

      <div style="font-size:.9rem;line-height:2;">
        <div>🟢 <b>Ponto forte:</b> {pf_forte}</div>
        <div>🔴 <b>Ponto fraco:</b> {pf_fraco}</div>
      </div>

      <div style="margin-top:14px;border-top:1px solid rgba(255,255,255,.1);
                  padding-top:14px;font-size:.85rem;line-height:1.8;color:#94a3b8;">
    """, unsafe_allow_html=True)

    # Notas individuais detalhadas
    for label, col in zip(labels_nota, colunas_nota):
        nota_val = float(row[col]) if pd.notna(row[col]) else 0.0
        media_col = df_f[col].mean()
        icone = "🟢" if nota_val >= media_col else "🔴"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;
                    border-bottom:1px solid rgba(255,255,255,.05);padding:3px 0;">
          <span>{icone} {label}</span>
          <span style="font-weight:700;color:#e7eefc;">{nota_val:.1f}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


# ── Tabela comparativa completa ───────────────────────────────────────────────
st.markdown('<p class="section-title">📋 Tabela Completa do Pelotão</p>', unsafe_allow_html=True)

df_display = df_f[[
    "ORD", "NOME", "NOTA_CORRIDA", "NOTA_ABDOMINAL",
    "NOTA_FLEXAO", "NOTA_NATACAO", "NOTA_BARRA",
    "MEDIA_FINAL", "CLASSIFICACAO", "PONTO_FRACO",
]].rename(columns={
    "ORD":            "Nº",
    "NOTA_CORRIDA":   "Corrida",
    "NOTA_ABDOMINAL": "Abdominal",
    "NOTA_FLEXAO":    "Flexão",
    "NOTA_NATACAO":   "Natação",
    "NOTA_BARRA":     "Barra",
    "MEDIA_FINAL":    "Média",
    "CLASSIFICACAO":  "Status",
    "PONTO_FRACO":    "Ponto Fraco",
})

def colorir_media(val):
    try:
        val = float(val)
    except (ValueError, TypeError):
        return ""
    if val >= 9.5:    return "background-color:rgba(34,197,94,.25);color:#bbf7d0"
    elif val >= 8.5:  return "background-color:rgba(59,130,246,.25);color:#bfdbfe"
    elif val >= 7.0:  return "background-color:rgba(245,158,11,.25);color:#fde68a"
    else:             return "background-color:rgba(239,68,68,.25);color:#fecaca"

styled = df_display.style.map(colorir_media, subset=["Média"])
st.dataframe(styled, use_container_width=True, height=420)


# ── Conclusões ────────────────────────────────────────────────────────────────
st.divider()
st.markdown('<p class="section-title">💡 Conclusões e Recomendações Operacionais</p>',
            unsafe_allow_html=True)

col_i1, col_i2, col_i3 = st.columns(3)

with col_i1:
    st.markdown("""
    #### 🎯 Treinamento direcionado
    Com base nos dados, o pelotão deve intensificar os treinos na
    disciplina com menor média coletiva. Um programa semanal específico
    pode elevar o desempenho geral em até 15% em 3 meses.
    """)
with col_i2:
    st.markdown("""
    #### 📅 Monitoramento contínuo
    Aplicar o TAF a cada bimestre permite acompanhar a evolução
    individual, detectar regressões precoces e ajustar o planejamento
    físico antes que o militar chegue a um nível crítico.
    """)
with col_i3:
    st.markdown("""
    #### 🤝 Mentoria entre pares
    Militares classificados como *Excelente* podem apoiar os
    classificados como *Atenção* em sessões de treino conjunto,
    fortalecendo o espírito de equipe e elevando a média do pelotão.
    """)

st.success(
    "**Conclusão · 3º Pelotão Japurá:** A análise de dados do TAF transforma uma avaliação pontual "
    "em uma ferramenta estratégica de gestão de pessoas. "
    "Conhecer o perfil físico de cada militar é fundamental para garantir "
    "a prontidão operacional, a segurança nas missões e o bem-estar da tropa."
)
