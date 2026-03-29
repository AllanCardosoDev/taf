# 🔥 CBMAM · Dashboard TAF

**Dashboard de Análise do Teste de Aptidão Física (TAF)**  
Corpo de Bombeiros Militar do Amazonas · 2026

## 📋 Sobre

Aplicação Streamlit para análise completa dos dados do TAF do CBMAM. O sistema processa dados de desempenho físico de militares em cinco disciplinas (corrida, abdominal, flexão, natação e barra), oferecendo visualizações interativas, rankings, comparativos e análises estatísticas.

## 🚀 Como executar

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar o dashboard
streamlit run taf.py
```

## 📊 Funcionalidades

### Páginas do Dashboard

| Página | Descrição |
|--------|-----------|
| 🏠 **Visão Geral** | KPIs, ranking, distribuição, radar Top 5 vs Bottom 5, mapa de calor, insights |
| 🪖 **Por Posto/Graduação** | Comparativo por posto, box plots, stacked bars, radar, taxa de ausência |
| 📋 **Por Quadro** | Análise por quadro (QCOBM, QCPBM, QPBM, etc.), radar comparativo |
| 👤 **Ficha Individual** | Perfil detalhado de cada militar com dados brutos e notas |
| 📈 **Estatísticas** | Box plots, distribuições, correlações, percentis, top/bottom 10 |
| ♿ **TAF Adaptado** | Dados dos militares no TAF modalidade adaptada |

### Filtros Globais (Sidebar)
- **Posto/Graduação**: MAJOR, CAP, 1° TEN, 2° TEN, ASP OF, ST, 1° SGT, 2° SGT, 3° SGT, CB, SD
- **Quadro**: QCOBM, QCPBM, QPBM, QOABM, QPEBM
- **Incluir ausentes**: Toggle para mostrar/ocultar militares que não compareceram
- **Média mínima**: Slider para filtrar por nota mínima

## 📁 Estrutura de Dados

O sistema usa **TAF.csv** como fonte única de dados. O CSV contém:

- **TAF Regular** (290 militares): Corrida 12min, Abdominal, Flexão, Natação 50m, Barra
- **TAF Adaptado** (46 militares): Caminhada, exercícios alternativos conforme aptidão individual

### Sistema de Pontuação

As notas (0-10) são calculadas a partir dos valores brutos de desempenho:

| Disciplina | Métrica | Nota 10 | Nota 8 | Nota 6 |
|------------|---------|---------|--------|--------|
| Corrida 12min | Metros (↑ melhor) | ≥ 2800m | ≥ 2400m | ≥ 2000m |
| Abdominal | Repetições (↑ melhor) | ≥ 48 | ≥ 38 | ≥ 28 |
| Flexão | Repetições (↑ melhor) | ≥ 38 | ≥ 28 | ≥ 18 |
| Natação 50m | Segundos (↓ melhor) | ≤ 35s | ≤ 45s | ≤ 55s |
| Barra Dinâmica | Repetições (↑ melhor) | ≥ 14 | ≥ 10 | ≥ 6 |
| Barra Estática | Segundos (↑ melhor) | ≥ 70s | ≥ 50s | ≥ 30s |

### Classificação

| Classificação | Média Final |
|---------------|-------------|
| 🟢 Excelente | ≥ 9,0 |
| 🔵 Bom | ≥ 7,5 |
| 🟡 Regular | ≥ 6,0 |
| 🔴 Insuficiente | < 6,0 |

## 🛠️ Tecnologias

- **Python 3.10+**
- **Streamlit** — Interface web interativa
- **Plotly** — Gráficos interativos
- **Pandas** — Processamento de dados
- **NumPy** — Cálculos numéricos

## 📂 Arquivos

```
taf.py          # Aplicação Streamlit principal
TAF.csv         # Dados do TAF (fonte única)
requirements.txt # Dependências Python
japura.enc      # Imagem do pelotão (opcional)
README.md       # Documentação
```

---

**CBMAM · BM-6/EMG · 2026** — Análise de Desempenho Físico
