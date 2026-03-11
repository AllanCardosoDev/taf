import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path

st.set_page_config(
    page_title="CBMAM · Dashboard TAF · Japurá",
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
cats = labels_nota + [labels_nota[0]]
cor_map = {
    "Excelente": "#22c55e",
    "Bom":       "#3b82f6",
    "Regular":   "#f59e0b",
    "Atenção":   "#ef4444",
}


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/"
        "Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Amazonas.svg/"
        "200px-Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Amazonas.svg.png",
        width=80,
    )
    st.markdown("## CBMAM · TAF")
    st.markdown("**3º Pelotão · Japurá**")
    st.divider()

    # Navegação por abas
    pagina = st.radio(
        "📌 Navegação",
        ["🏠 Visão Geral", "🪖 Ficha Individual"],
        label_visibility="collapsed",
    )

    st.divider()

    # Filtros (apenas visão geral)
    if pagina == "🏠 Visão Geral":
        st.markdown("**Filtros**")
        classificacoes = ["Todos"] + sorted(df["CLASSIFICACAO"].unique().tolist())
        filtro_class = st.selectbox("Classificação", classificacoes)
        nota_minima  = st.slider("Média mínima", 0.0, 10.0,
                                 float(df["MEDIA_FINAL"].min()), 0.1)
    else:
        filtro_class = "Todos"
        nota_minima  = 0.0

        st.markdown("**🔎 Selecionar Militar**")
        busca_sb = st.text_input("Buscar por nome", placeholder="Digite parte do nome...")

        lista_nomes = df["NOME"].tolist()
        if busca_sb:
            lista_nomes = [n for n in lista_nomes if busca_sb.upper() in n]

        if lista_nomes:
            militar_sel = st.selectbox("Militar", lista_nomes)
        else:
            st.warning("Nenhum militar encontrado.")
            militar_sel = df["NOME"].tolist()[0]

    st.divider()
    st.markdown(
        "<small>CBMAM · BM-6/EMG · 2026<br>Análise de Desempenho Físico</small>",
        unsafe_allow_html=True,
    )


# ── Filtro df ─────────────────────────────────────────────────────────────────
df_f = df.copy()
if filtro_class != "Todos":
    df_f = df_f[df_f["CLASSIFICACAO"] == filtro_class]
df_f = df_f[df_f["MEDIA_FINAL"] >= nota_minima]


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "🏠 Visão Geral":

    # Cabeçalho
    col_txt, col_img = st.columns([2.2, 1])
    with col_txt:
        st.markdown("""
        <h1 style="margin:0;font-size:2rem;">🔥 Avaliação Prática · TAF</h1>
        <p style="margin:6px 0 12px;color:#94a3b8;">
          Corpo de Bombeiros Militar do Amazonas &nbsp;·&nbsp;
          3º Pelotão · Japurá &nbsp;·&nbsp; 2026
        </p>
        """, unsafe_allow_html=True)
        st.markdown("""
        > **Por que analisar dados do TAF?**
        > O acompanhamento sistemático do desempenho físico permite identificar pontos
        > críticos, orientar treinamentos direcionados e elevar o nível operacional da
        > corporação. Dados bem analisados salvam vidas — dentro e fora do quartel.
        """)

    with col_img:
        foto = Path("japura.enc")
        if foto.exists():
            st.image(
                str(foto),
                caption="3º Pelotão · Japurá · CBMAM",
                use_container_width=True,
            )

    st.divider()

    # KPIs
    st.markdown('<p class="section-title">📊 Visão Geral do Pelotão · Japurá</p>',
                unsafe_allow_html=True)

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

    # Ranking
    st.markdown('<p class="section-title">🏆 Ranking — Média Final</p>',
                unsafe_allow_html=True)

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

    # Distribuição
    st.markdown('<p class="section-title">📉 Distribuição de Desempenho</p>',
                unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        contagem = df_f["CLASSIFICACAO"].value_counts().reset_index()
        contagem.columns = ["Classificação", "Quantidade"]
        ordem = ["Excelente", "Bom", "Regular", "Atenção"]
        contagem["Classificação"] = pd.Categorical(
            contagem["Classificação"], categories=ordem, ordered=True
        )
        fig_pie = px.pie(
            contagem.sort_values("Classificação"),
            names="Classificação", values="Quantidade",
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

    # Média por disciplina
    st.markdown('<p class="section-title">💪 Desempenho Médio por Disciplina</p>',
                unsafe_allow_html=True)

    medias_disc = {l: df_f[c].mean() for l, c in zip(labels_nota, colunas_nota)}
    df_disc = pd.DataFrame({
        "Disciplina": list(medias_disc.keys()),
        "Média":      list(medias_disc.values()),
    }).sort_values("Média")

    fig_disc = px.bar(
        df_disc, x="Média", y="Disciplina", orientation="h", text="Média",
        color="Disciplina",
        color_discrete_sequence=["#ef4444" if v < 9.0 else "#22c55e" for v in df_disc["Média"]],
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

    st.info(
        f"**📌 Insight automático — Japurá:** A disciplina com menor média é "
        f"**{df_disc.iloc[0]['Disciplina']}** ({df_disc.iloc[0]['Média']:.2f}). "
        f"O ponto forte do pelotão é **{df_disc.iloc[-1]['Disciplina']}**."
    )

    # Radar Top 5 vs Bottom 5
    st.markdown('<p class="section-title">🕸️ Radar — Top 5 vs Bottom 5</p>',
                unsafe_allow_html=True)

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
        title="Comparativo de perfil físico — 3º Pelotão Japurá",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Mapa de calor
    st.markdown('<p class="section-title">🌡️ Mapa de Calor — Notas individuais</p>',
                unsafe_allow_html=True)

    df_heat = df_f[["NOME"] + colunas_nota].copy()
    df_heat["NOME_CURTO"] = df_heat["NOME"].apply(lambda x: " ".join(str(x).split()[:2]))
    df_heat = df_heat.sort_values("NOTA_CORRIDA", ascending=False)

    z_vals = df_heat[colunas_nota].values.tolist()

    fig_heat = go.Figure(go.Heatmap(
        z=z_vals, x=labels_nota, y=df_heat["NOME_CURTO"].tolist(),
        colorscale=[[0.0,"#ef4444"],[0.5,"#f59e0b"],[0.75,"#3b82f6"],[1.0,"#22c55e"]],
        zmin=0, zmax=10,
        text=[[f"{v:.1f}" if pd.notna(v) else "—" for v in row] for row in z_vals],
        texttemplate="%{text}",
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>",
        colorbar=dict(title="Nota", tickfont_color="#e7eefc", title_font_color="#e7eefc"),
    ))
    fig_heat.update_layout(
        height=max(500, len(df_heat) * 22),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e7eefc", margin=dict(l=10, r=10, t=20, b=20),
        xaxis=dict(side="top"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Pontos fracos
    st.markdown('<p class="section-title">🔍 Disciplinas com Mais Pontos Fracos</p>',
                unsafe_allow_html=True)

    pf_df = df_f["PONTO_FRACO"].value_counts().reset_index()
    pf_df.columns = ["Disciplina", "Quantidade"]

    fig_pf = px.bar(
        pf_df, x="Disciplina", y="Quantidade",
        color="Quantidade", color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],
        text="Quantidade", title="Disciplina onde cada militar tem sua pior nota",
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
    st.warning(
        f"⚠️ **{pf_df.iloc[0]['Quantidade']} militares** têm seu pior desempenho em "
        f"**{pf_df.iloc[0]['Disciplina']}**. Recomenda-se treino focado nessa modalidade."
    )

    # Correlação
    st.markdown('<p class="section-title">🏃 Correlação: Corrida 12min × Média Final</p>',
                unsafe_allow_html=True)

    fig_scatter = px.scatter(
        df_f, x="CORRIDA_12MIN", y="MEDIA_FINAL",
        color="CLASSIFICACAO", color_discrete_map=cor_map,
        size="MEDIA_FINAL", hover_name="NOME",
        trendline="ols", trendline_color_override="#ffffff",
        labels={"CORRIDA_12MIN":"Metros (12 min)","MEDIA_FINAL":"Média Final"},
        title="Militares com maior distância na corrida tendem a ter média mais alta?",
    )
    fig_scatter.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e7eefc",
        yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
        xaxis=dict(gridcolor="rgba(255,255,255,.06)"),
        margin=dict(t=50, b=20), height=420,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Tabela
    st.markdown('<p class="section-title">📋 Tabela Completa — 3º Pelotão Japurá</p>',
                unsafe_allow_html=True)

    df_display = df_f[[
        "ORD","NOME","NOTA_CORRIDA","NOTA_ABDOMINAL",
        "NOTA_FLEXAO","NOTA_NATACAO","NOTA_BARRA",
        "MEDIA_FINAL","CLASSIFICACAO","PONTO_FRACO",
    ]].rename(columns={
        "ORD":"Nº","NOTA_CORRIDA":"Corrida","NOTA_ABDOMINAL":"Abdominal",
        "NOTA_FLEXAO":"Flexão","NOTA_NATACAO":"Natação","NOTA_BARRA":"Barra",
        "MEDIA_FINAL":"Média","CLASSIFICACAO":"Status","PONTO_FRACO":"Ponto Fraco",
    })

    def colorir(val):
        try:
            v = float(val)
        except:
            return ""
        if v >= 9.5:   return "background-color:rgba(34,197,94,.25);color:#bbf7d0"
        elif v >= 8.5: return "background-color:rgba(59,130,246,.25);color:#bfdbfe"
        elif v >= 7.0: return "background-color:rgba(245,158,11,.25);color:#fde68a"
        else:          return "background-color:rgba(239,68,68,.25);color:#fecaca"

    st.dataframe(
        df_display.style.map(colorir, subset=["Média"]),
        use_container_width=True, height=420,
    )

    # Conclusões
    st.divider()
    st.markdown('<p class="section-title">💡 Conclusões e Recomendações — Japurá</p>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        #### 🎯 Treinamento direcionado
        Com base nos dados, o pelotão deve intensificar os treinos na
        disciplina com menor média coletiva. Um programa semanal específico
        pode elevar o desempenho geral em até 15% em 3 meses.
        """)
    with c2:
        st.markdown("""
        #### 📅 Monitoramento contínuo
        Aplicar o TAF a cada bimestre permite acompanhar a evolução
        individual e detectar regressões antes que o militar
        chegue a um nível crítico.
        """)
    with c3:
        st.markdown("""
        #### 🤝 Mentoria entre pares
        Militares *Excelente* podem apoiar os de *Atenção* em sessões
        conjuntas, fortalecendo o espírito de equipe e elevando
        a média do 3º Pelotão Japurá.
        """)

    st.success(
        "**Conclusão · 3º Pelotão Japurá:** A análise de dados do TAF transforma uma "
        "avaliação pontual em ferramenta estratégica de gestão de pessoas. "
        "Conhecer o perfil físico de cada militar garante prontidão operacional, "
        "segurança nas missões e bem-estar da tropa."
    )


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: FICHA INDIVIDUAL
# ══════════════════════════════════════════════════════════════════════════════
else:
    row        = df[df["NOME"] == militar_sel].iloc[0]
    vals_ind   = [float(row[c]) if pd.notna(row[c]) else 0.0 for c in colunas_nota]
    nome_curto = " ".join(str(militar_sel).split()[:2])
    media_ind  = float(row["MEDIA_FINAL"])
    class_ind  = row["CLASSIFICACAO"]
    media_pel  = df["MEDIA_FINAL"].mean()
    diff       = media_ind - media_pel
    sinal      = "+" if diff >= 0 else ""
    cor_diff   = "#22c55e" if diff >= 0 else "#ef4444"

    rank_pos = df["MEDIA_FINAL"].rank(ascending=False, method="min")
    posicao  = int(rank_pos[df["NOME"] == militar_sel].values[0])
    total    = len(df)

    pf_notas = {l: float(row[c]) for l, c in zip(labels_nota, colunas_nota) if pd.notna(row[c])}
    pf_forte = max(pf_notas, key=pf_notas.get) if pf_notas else "—"
    pf_fraco = row["PONTO_FRACO"]

    badge_cor = {
        "Excelente": ("#bbf7d0", "#166534", "rgba(34,197,94,.3)"),
        "Bom":       ("#bfdbfe", "#1e3a5f", "rgba(59,130,246,.3)"),
        "Regular":   ("#fde68a", "#78350f", "rgba(245,158,11,.3)"),
        "Atenção":   ("#fecaca", "#7f1d1d", "rgba(239,68,68,.3)"),
    }.get(class_ind, ("#e7eefc", "#1e293b", "rgba(255,255,255,.1)"))

    # Cabeçalho da ficha
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(239,68,68,.15),rgba(59,130,246,.1));
                border:1px solid rgba(239,68,68,.3);border-radius:16px;
                padding:24px 28px;margin-bottom:20px;">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
        <div>
          <div style="font-size:1.8rem;font-weight:800;">🪖 {nome_curto}</div>
          <div style="color:#94a3b8;margin-top:4px;">
            3º Pelotão · Japurá · CBMAM · 2026
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
            <div style="font-size:1.3rem;font-weight:800;">{posicao}º / {total}</div>
          </div>
          <div style="background:rgba(255,255,255,.05);border-radius:12px;padding:10px 20px;text-align:center;">
            <div style="font-size:.75rem;color:#94a3b8;">vs PELOTÃO</div>
            <div style="font-size:1.3rem;font-weight:800;color:{cor_diff};">{sinal}{diff:.2f}</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Gráficos
    col_r, col_b2 = st.columns(2)

    with col_r:
        st.markdown('<p class="section-title">🕸️ Radar de Atributos</p>',
                    unsafe_allow_html=True)

        med_pel_vals = [df[c].mean() for c in colunas_nota]

        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(
            r=[10]*len(cats), theta=cats, fill="toself", name="Máximo",
            line_color="rgba(255,255,255,.1)", fillcolor="rgba(255,255,255,.03)",
        ))
        fig_r.add_trace(go.Scatterpolar(
            r=med_pel_vals + [med_pel_vals[0]], theta=cats,
            fill="toself", name="Média Pelotão",
            line_color="#f59e0b", fillcolor="rgba(245,158,11,.1)",
            line_dash="dot",
        ))
        fig_r.add_trace(go.Scatterpolar(
            r=vals_ind + [vals_ind[0]], theta=cats,
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
            paper_bgcolor="rgba(0,0,0,0)", font_color="#e7eefc",
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            height=440, margin=dict(t=30, b=60),
        )
        st.plotly_chart(fig_r, use_container_width=True)

    with col_b2:
        st.markdown('<p class="section-title">📊 Notas vs Média do Pelotão</p>',
                    unsafe_allow_html=True)

        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            name="Média Pelotão", x=labels_nota, y=med_pel_vals,
            marker_color="rgba(245,158,11,.5)",
            text=[f"{v:.1f}" for v in med_pel_vals],
            textposition="outside",
        ))
        fig_b.add_trace(go.Bar(
            name=nome_curto, x=labels_nota, y=vals_ind,
            marker_color=[
                "#22c55e" if n >= m else "#ef4444"
                for n, m in zip(vals_ind, med_pel_vals)
            ],
            text=[f"{v:.1f}" for v in vals_ind],
            textposition="outside",
        ))
        fig_b.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e7eefc",
            yaxis=dict(range=[0, 12], gridcolor="rgba(255,255,255,.06)"),
            xaxis=dict(gridcolor="rgba(255,255,255,.06)"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25),
            height=440, margin=dict(t=30, b=60),
        )
        st.plotly_chart(fig_b, use_container_width=True)

    # Cards de notas + gráfico gauge média
    st.markdown('<p class="section-title">🎯 Detalhamento por Disciplina</p>',
                unsafe_allow_html=True)

    cols_disc = st.columns(5)
    for i, (label, col_n) in enumerate(zip(labels_nota, colunas_nota)):
        nota_v  = float(row[col_n]) if pd.notna(row[col_n]) else 0.0
        med_v   = df[col_n].mean()
        delta_v = nota_v - med_v
        s       = "+" if delta_v >= 0 else ""
        c_delta = "#22c55e" if delta_v >= 0 else "#ef4444"
        icone   = "🟢" if nota_v >= med_v else "🔴"

        with cols_disc[i]:
            st.markdown(f"""
            <div style="background:rgba(17,27,46,.8);border:1px solid rgba(255,255,255,.1);
                        border-radius:14px;padding:16px;text-align:center;">
              <div style="font-size:.8rem;color:#94a3b8;margin-bottom:8px;">{label}</div>
              <div style="font-size:2rem;font-weight:800;">{nota_v:.1f}</div>
              <div style="font-size:.8rem;color:{c_delta};margin-top:4px;">
                {icone} {s}{delta_v:.2f} vs pelotão
              </div>
              <div style="background:rgba(255,255,255,.06);border-radius:6px;
                          margin-top:10px;height:6px;overflow:hidden;">
                <div style="width:{nota_v*10}%;height:100%;
                             background:{'#22c55e' if nota_v >= 9.5 else '#3b82f6' if nota_v >= 8.5 else '#f59e0b' if nota_v >= 7.0 else '#ef4444'};
                             border-radius:6px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # Gauge média final
    st.markdown('<p class="section-title">🏁 Indicador de Média Final</p>',
                unsafe_allow_html=True)

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=media_ind,
        delta={"reference": media_pel, "valueformat": ".2f",
               "increasing": {"color": "#22c55e"},
               "decreasing": {"color": "#ef4444"}},
        title={"text": f"Média Final · {nome_curto}<br><span style='font-size:.8rem;color:#94a3b8'>Referência: média do pelotão ({media_pel:.2f})</span>"},
        gauge={
            "axis": {"range": [0, 10], "tickcolor": "#94a3b8"},
            "bar":  {"color": cor_map.get(class_ind, "#3b82f6")},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": "rgba(255,255,255,.1)",
            "steps": [
                {"range": [0,   7.0], "color": "rgba(239,68,68,.15)"},
                {"range": [7.0, 8.5], "color": "rgba(245,158,11,.15)"},
                {"range": [8.5, 9.5], "color": "rgba(59,130,246,.15)"},
                {"range": [9.5, 10],  "color": "rgba(34,197,94,.15)"},
            ],
            "threshold": {
                "line": {"color": "#f59e0b", "width": 3},
                "thickness": 0.8,
                "value": media_pel,
            },
        },
        number={"font": {"color": "#e7eefc", "size": 56}},
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font_color="#e7eefc",
        height=320, margin=dict(t=60, b=20, l=40, r=40),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Resumo textual
    st.markdown(f"""
    <div style="background:rgba(17,27,46,.8);border:1px solid rgba(255,255,255,.1);
                border-radius:14px;padding:20px;margin-top:10px;line-height:2;">
      <b>🟢 Ponto forte:</b> {pf_forte} ({pf_notas.get(pf_forte, 0):.1f})<br>
      <b>🔴 Ponto fraco:</b> {pf_fraco} ({pf_notas.get(pf_fraco, 0):.1f})<br>
      <b>📍 Posição no ranking:</b> {posicao}º de {total} militares avaliados<br>
      <b>📈 Diferença vs média do pelotão ({media_pel:.2f}):</b>
      <span style="color:{cor_diff};font-weight:700;">{sinal}{diff:.2f} pontos</span>
    </div>
    """, unsafe_allow_html=True)
