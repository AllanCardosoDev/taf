import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="CBMAM · Dashboard TAF",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS customizado ───────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* fundo geral */
  [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0b1220 0%, #0f172a 100%);
    color: #e7eefc;
  }
  [data-testid="stSidebar"] {
    background: #111b2e;
    border-right: 1px solid rgba(255,255,255,.08);
  }
  /* cards de métricas */
  [data-testid="metric-container"] {
    background: rgba(17,27,46,.8);
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 14px;
    padding: 18px 20px;
  }
  /* cabeçalho de seção */
  .section-title {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: .5px;
    color: #ef4444;
    margin: 28px 0 8px;
    border-left: 4px solid #ef4444;
    padding-left: 10px;
  }
  /* badge */
  .badge {
    display: inline-block;
    background: rgba(239,68,68,.18);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,.4);
    border-radius: 999px;
    padding: 3px 12px;
    font-size: .85rem;
    font-weight: 600;
  }
  /* rodapé */
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Carregamento e preparação dos dados ──────────────────────────────────────
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados.csv")

    # Classificação de desempenho
    def classificar(media):
        if media >= 9.5:
            return "Excelente"
        elif media >= 8.5:
            return "Bom"
        elif media >= 7.0:
            return "Regular"
        else:
            return "Atenção"

    df["CLASSIFICACAO"] = df["MEDIA_FINAL"].apply(classificar)

    # Identifica pontos fracos por aluno
    notas = {
        "Corrida 12min":    "NOTA_CORRIDA",
        "Abdominal":        "NOTA_ABDOMINAL",
        "Flexão de Braços": "NOTA_FLEXAO",
        "Natação 50m":      "NOTA_NATACAO",
        "Barra":            "NOTA_BARRA",
    }
    def ponto_fraco(row):
        menores = {k: row[v] for k, v in notas.items()}
        return min(menores, key=menores.get)

    df["PONTO_FRACO"] = df.apply(ponto_fraco, axis=1)
    return df, notas


df, notas = carregar_dados()
colunas_nota = list(notas.values())
labels_nota  = list(notas.keys())


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/"
        "Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Amazonas.svg/"
        "200px-Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Amazonas.svg.png",
        width=90,
    )
    st.markdown("## CBMAM · TAF Dashboard")
    st.markdown("**3º Pelotão · Japur**")
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


# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:6px;">
  <div>
    <h1 style="margin:0;font-size:2rem;">
      🔥 Avaliação Prática · TAF
    </h1>
    <p style="margin:4px 0 0;color:#94a3b8;">
      Corpo de Bombeiros Militar do Amazonas &nbsp;·&nbsp;
      3º Pelotão · Japur &nbsp;·&nbsp; 2026
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
> **Por que analisar dados do TAF?**  
> O acompanhamento sistemático do desempenho físico dos militares permite identificar
> pontos críticos de melhoria individual e coletiva, orientar treinamentos direcionados,
> prevenir afastamentos por lesão e elevar o nível operacional da corporação.
> Dados bem analisados salvam vidas — dentro e fora do quartel.
""")

st.divider()


# ── KPIs principais ───────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📊 Visão Geral do Pelotão</p>', unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)

media_geral   = df_f["MEDIA_FINAL"].mean()
melhor        = df_f.loc[df_f["MEDIA_FINAL"].idxmax()]
pior          = df_f.loc[df_f["MEDIA_FINAL"].idxmin()]
excelentes    = len(df_f[df_f["CLASSIFICACAO"] == "Excelente"])
atencao       = len(df_f[df_f["CLASSIFICACAO"] == "Atenção"])
aprovados     = len(df_f[df_f["MEDIA_FINAL"] >= 7.0])

k1.metric("👥 Militares avaliados", len(df_f))
k2.metric("📈 Média geral do pelotão", f"{media_geral:.2f}")
k3.metric("🥇 Maior média", f"{melhor['MEDIA_FINAL']:.1f}",
          melhor["NOME"].split()[0])
k4.metric("⚠️ Menor média", f"{pior['MEDIA_FINAL']:.1f}",
          pior["NOME"].split()[0])
k5.metric("✅ Excelentes (≥ 9,5)", excelentes)
k6.metric("🚨 Atenção (< 7,0)", atencao)

st.divider()


# ── Gráfico 1: Ranking geral ──────────────────────────────────────────────────
st.markdown('<p class="section-title">🏆 Ranking de Desempenho — Média Final</p>', unsafe_allow_html=True)

df_rank = df_f.sort_values("MEDIA_FINAL", ascending=True).copy()
df_rank["NOME_CURTO"] = df_rank["NOME"].apply(
    lambda x: " ".join(x.split()[:2])
)

cor_map = {
    "Excelente": "#22c55e",
    "Bom":       "#3b82f6",
    "Regular":   "#f59e0b",
    "Atenção":   "#ef4444",
}
df_rank["COR"] = df_rank["CLASSIFICACAO"].map(cor_map)

fig_rank = px.bar(
    df_rank,
    x="MEDIA_FINAL",
    y="NOME_CURTO",
    orientation="h",
    color="CLASSIFICACAO",
    color_discrete_map=cor_map,
    text="MEDIA_FINAL",
    hover_data={"NOME": True, "MEDIA_FINAL": True, "CLASSIFICACAO": True},
    labels={"MEDIA_FINAL": "Média Final", "NOME_CURTO": ""},
)
fig_rank.update_traces(texttemplate="%{text:.1f}", textposition="outside")
fig_rank.update_layout(
    height=max(500, len(df_rank) * 22),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc",
    legend_title_text="Classificação",
    xaxis=dict(range=[0, 11], gridcolor="rgba(255,255,255,.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    margin=dict(l=10, r=60, t=20, b=20),
)
st.plotly_chart(fig_rank, use_container_width=True)


# ── Gráfico 2: Distribuição por classificação + histograma ───────────────────
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
        contagem,
        names="Classificação",
        values="Quantidade",
        color="Classificação",
        color_discrete_map=cor_map,
        hole=0.52,
        title="Proporção por classificação",
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e7eefc",
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
        x=media_geral, line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"Média: {media_geral:.2f}",
        annotation_font_color="#ef4444",
    )
    fig_hist.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e7eefc",
        margin=dict(t=50, b=10),
        yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
        xaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    )
    st.plotly_chart(fig_hist, use_container_width=True)


# ── Gráfico 3: Média por disciplina ──────────────────────────────────────────
st.markdown('<p class="section-title">💪 Desempenho Médio por Disciplina</p>', unsafe_allow_html=True)

medias_disc = {label: df_f[col].mean() for label, col in zip(labels_nota, colunas_nota)}
df_disc = pd.DataFrame({
    "Disciplina": list(medias_disc.keys()),
    "Média":      list(medias_disc.values()),
})
df_disc = df_disc.sort_values("Média")

cores_disc = ["#ef4444" if v < 9.0 else "#22c55e" for v in df_disc["Média"]]

fig_disc = px.bar(
    df_disc, x="Média", y="Disciplina",
    orientation="h",
    text="Média",
    color="Disciplina",
    color_discrete_sequence=cores_disc,
    labels={"Média": "Nota Média", "Disciplina": ""},
    title="Onde o pelotão se sai melhor e pior",
)
fig_disc.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside",
    showlegend=False,
)
fig_disc.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc",
    xaxis=dict(range=[0, 11], gridcolor="rgba(255,255,255,.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    margin=dict(l=10, r=70, t=50, b=20),
    height=320,
)
st.plotly_chart(fig_disc, use_container_width=True)

# ── Insight automático ────────────────────────────────────────────────────────
disciplina_mais_fraca = df_disc.iloc[0]["Disciplina"]
nota_mais_fraca       = df_disc.iloc[0]["Média"]
disciplina_mais_forte = df_disc.iloc[-1]["Disciplina"]

st.info(
    f"**📌 Insight automático:** A disciplina com menor média coletiva é "
    f"**{disciplina_mais_fraca}** ({nota_mais_fraca:.2f}), indicando necessidade "
    f"de atenção no treinamento específico dessa modalidade. "
    f"O ponto forte do pelotão é **{disciplina_mais_forte}**."
)


# ── Gráfico 4: Radar comparativo (Top 5 vs Bottom 5) ─────────────────────────
st.markdown('<p class="section-title">🕸️ Radar de Perfil — Top 5 vs Bottom 5</p>', unsafe_allow_html=True)

top5    = df_f.nlargest(5,  "MEDIA_FINAL")[colunas_nota].mean().tolist()
bottom5 = df_f.nsmallest(5, "MEDIA_FINAL")[colunas_nota].mean().tolist()
cats    = labels_nota + [labels_nota[0]]

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=top5 + [top5[0]], theta=cats,
    fill="toself", name="Top 5",
    line_color="#22c55e",
    fillcolor="rgba(34,197,94,.15)",
))
fig_radar.add_trace(go.Scatterpolar(
    r=bottom5 + [bottom5[0]], theta=cats,
    fill="toself", name="Bottom 5",
    line_color="#ef4444",
    fillcolor="rgba(239,68,68,.15)",
))
fig_radar.update_layout(
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(
            visible=True, range=[0, 10],
            gridcolor="rgba(255,255,255,.12)",
            tickfont_color="#94a3b8",
        ),
        angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc",
    legend=dict(orientation="h", yanchor="bottom", y=-0.15),
    height=420,
    title="Comparativo de perfil físico entre os extremos do pelotão",
)
st.plotly_chart(fig_radar, use_container_width=True)


# ── Gráfico 5: Mapa de calor ──────────────────────────────────────────────────
st.markdown('<p class="section-title">🌡️ Mapa de Calor — Notas individuais por disciplina</p>',
            unsafe_allow_html=True)

df_heat = df_f[["NOME"] + colunas_nota].copy()
df_heat["NOME_CURTO"] = df_heat["NOME"].apply(lambda x: " ".join(x.split()[:2]))
df_heat = df_heat.sort_values("NOTA_CORRIDA", ascending=False)

z_vals = df_heat[colunas_nota].values
nomes  = df_heat["NOME_CURTO"].tolist()

fig_heat = go.Figure(go.Heatmap(
    z=z_vals,
    x=labels_nota,
    y=nomes,
    colorscale=[
        [0.0,  "#ef4444"],
        [0.5,  "#f59e0b"],
        [0.75, "#3b82f6"],
        [1.0,  "#22c55e"],
    ],
    zmin=0, zmax=10,
    text=[[f"{v:.1f}" for v in row] for row in z_vals],
    texttemplate="%{text}",
    hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>",
    colorbar=dict(title="Nota", tickfont_color="#e7eefc", title_font_color="#e7eefc"),
))
fig_heat.update_layout(
    height=max(500, len(df_heat) * 22),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc",
    margin=dict(l=10, r=10, t=20, b=20),
    xaxis=dict(side="top"),
)
st.plotly_chart(fig_heat, use_container_width=True)


# ── Gráfico 6: Pontos fracos mais frequentes ─────────────────────────────────
st.markdown('<p class="section-title">🔍 Disciplinas com Mais Pontos Fracos</p>',
            unsafe_allow_html=True)

pontos_fracos = df_f["PONTO_FRACO"].value_counts().reset_index()
pontos_fracos.columns = ["Disciplina", "Quantidade"]

fig_pf = px.bar(
    pontos_fracos,
    x="Disciplina", y="Quantidade",
    color="Quantidade",
    color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
    text="Quantidade",
    title="Disciplina onde cada militar tem sua pior nota",
    labels={"Quantidade": "Nº de militares", "Disciplina": ""},
)
fig_pf.update_traces(textposition="outside")
fig_pf.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc",
    coloraxis_showscale=False,
    yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    xaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    margin=dict(t=50, b=20),
    height=350,
)
st.plotly_chart(fig_pf, use_container_width=True)

disciplina_critica = pontos_fracos.iloc[0]["Disciplina"]
qtd_critica        = pontos_fracos.iloc[0]["Quantidade"]
st.warning(
    f"⚠️ **{qtd_critica} militares** têm seu pior desempenho em "
    f"**{disciplina_critica}**. Recomenda-se treino focado nessa modalidade."
)


# ── Gráfico 7: Corrida × Média Final (correlação) ────────────────────────────
st.markdown('<p class="section-title">🏃 Correlação: Corrida 12min × Média Final</p>',
            unsafe_allow_html=True)

fig_scatter = px.scatter(
    df_f,
    x="CORRIDA_12MIN", y="MEDIA_FINAL",
    color="CLASSIFICACAO",
    color_discrete_map=cor_map,
    size="MEDIA_FINAL",
    hover_name="NOME",
    trendline="ols",
    trendline_color_override="#ffffff",
    labels={
        "CORRIDA_12MIN": "Metros percorridos (12 min)",
        "MEDIA_FINAL":   "Média Final",
    },
    title="Militares com maior distância na corrida tendem a ter média final mais alta?",
)
fig_scatter.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e7eefc",
    yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    xaxis=dict(gridcolor="rgba(255,255,255,.06)"),
    margin=dict(t=50, b=20),
    height=420,
)
st.plotly_chart(fig_scatter, use_container_width=True)


# ── Tabela detalhada individual ───────────────────────────────────────────────
st.markdown('<p class="section-title">📋 Ficha Individual — Consulta por militar</p>',
            unsafe_allow_html=True)

busca = st.text_input("🔎 Buscar militar pelo nome")
df_tabela = df_f.copy()
if busca:
    df_tabela = df_tabela[
        df_tabela["NOME"].str.contains(busca.upper(), na=False)
    ]

# Selecionar militar para ver radar individual
militar_selecionado = st.selectbox(
    "Selecione um militar para ver o perfil radar individual",
    df_tabela["NOME"].tolist(),
)

col_tab, col_radar_ind = st.columns([1.6, 1])

with col_tab:
    df_display = df_tabela[[
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
        if val >= 9.5:
            return "background-color: rgba(34,197,94,.25); color:#bbf7d0"
        elif val >= 8.5:
            return "background-color: rgba(59,130,246,.25); color:#bfdbfe"
        elif val >= 7.0:
            return "background-color: rgba(245,158,11,.25); color:#fde68a"
        else:
            return "background-color: rgba(239,68,68,.25); color:#fecaca"

    styled = df_display.style.applymap(colorir_media, subset=["Média"])
    st.dataframe(styled, use_container_width=True, height=420)

with col_radar_ind:
    row = df_f[df_f["NOME"] == militar_selecionado].iloc[0]
    vals_ind = [row[c] for c in colunas_nota]
    nome_curto = " ".join(militar_selecionado.split()[:2])

    fig_ind = go.Figure(go.Scatterpolar(
        r=vals_ind + [vals_ind[0]],
        theta=cats,
        fill="toself",
        name=nome_curto,
        line_color="#3b82f6",
        fillcolor="rgba(59,130,246,.2)",
    ))
    fig_ind.add_trace(go.Scatterpolar(
        r=[10]*len(cats),
        theta=cats,
        fill="toself",
        name="Máximo",
        line_color="rgba(255,255,255,.15)",
        fillcolor="rgba(255,255,255,.04)",
    ))
    fig_ind.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 10],
                gridcolor="rgba(255,255,255,.12)",
                tickfont_color="#94a3b8",
            ),
            angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e7eefc",
        title=f"Perfil: {nome_curto}<br><sup>Média: {row['MEDIA_FINAL']:.1f} · {row['CLASSIFICACAO']}</sup>",
        height=400,
        showlegend=False,
        margin=dict(t=80, b=20),
    )
    st.plotly_chart(fig_ind, use_container_width=True)

    # Mini-cards do militar
    st.markdown(f"""
    <div style="background:rgba(17,27,46,.8);border:1px solid rgba(255,255,255,.1);
                border-radius:12px;padding:14px;font-size:.9rem;line-height:1.8;">
      <b>Ponto forte:</b> {max({l: row[c] for l, c in zip(labels_nota, colunas_nota)}, key=lambda k: {l: row[c] for l, c in zip(labels_nota, colunas_nota)}[k])}<br>
      <b>Ponto fraco:</b> {row['PONTO_FRACO']}<br>
      <b>Média final:</b> {row['MEDIA_FINAL']:.1f}<br>
      <b>Classificação:</b> {row['CLASSIFICACAO']}
    </div>
    """, unsafe_allow_html=True)


# ── Insights finais ───────────────────────────────────────────────────────────
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
    "**Conclusão:** A análise de dados do TAF transforma uma avaliação pontual "
    "em uma ferramenta estratégica de gestão de pessoas. "
    "Conhecer o perfil físico de cada militar é fundamental para garantir "
    "a prontidão operacional, a segurança nas missões e o bem-estar da tropa."
)
