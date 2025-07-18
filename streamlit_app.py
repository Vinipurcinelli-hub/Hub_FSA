import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# === CONFIGURAÇÃO STREAMLIT ===
st.set_page_config(layout="wide")
st.title("🕒 Timeline Interativa com Zoom Inteligente")

# === LEITURA DA PLANILHA ===
arquivo = r"C:\Users\vpurcinelli\Documents\estudo_hub_fsa\estudo_linhas\GANT\Planejamento operacional.xlsx"
df = pd.read_excel(arquivo)

# === PREPARAÇÃO DOS DADOS ===
df["Início"] = pd.to_datetime(df["Início"])
df["Fim"] = pd.to_datetime(df["Fim"])
df["Duração_h"] = (df["Fim"] - df["Início"]).dt.total_seconds() / 3600
inicio_base = df["Início"].min().replace(hour=0, minute=0, second=0, microsecond=0)
df["Hora_absoluta"] = (df["Início"] - inicio_base).dt.total_seconds() / 3600

# Cores únicas por empresa
cores = {
    "GUANABARA": "royalblue",
    "HUB": "firebrick",
    "ITAPEMIRIM": "gold"
}
df["Cor"] = df["Empresa"].map(cores).fillna("gray")

# Mapear as linhas no eixo Y
linhas_unicas = df["Linha"].unique()
mapa_linhas = {linha: i for i, linha in enumerate(linhas_unicas)}
df["Linha_Y"] = df["Linha"].map(mapa_linhas)

# === CONSTRUÇÃO DO GRÁFICO ===
fig = go.Figure()

# Agrupar por empresa para performance e legenda única
for empresa, grupo in df.groupby("Empresa"):
    fig.add_trace(go.Bar(
        x=grupo["Duração_h"],
        y=grupo["Linha"],
        base=grupo["Hora_absoluta"],
        orientation='h',
        marker=dict(color=cores.get(empresa, "gray")),
        name=empresa,
        legendgroup=empresa,
        hovertemplate=(
            "<b>%{y}</b><br>" +
            "Etapa: %{customdata[0]}<br>" +
            "Início: %{customdata[1]}<br>" +
            "Fim: %{customdata[2]}<br>" +
            "Duração: %{x:.1f}h<br>" +
            "Empresa: %{customdata[3]}"
        ),
        customdata=grupo[["Etapa", "Início", "Fim", "Empresa"]].values
    ))

# === CONFIGURAÇÃO VISUAL ===
fig.update_layout(
    barmode='stack',
    bargap=0.2,
    dragmode='pan',
    xaxis=dict(
        title="Hora do dia (desde início)",
        tickmode="auto",
        showgrid=True,
        ticks="outside",
        ticklen=6,
        tickfont=dict(size=10),
    ),
    yaxis=dict(
        title="Linha Operacional",
        autorange="reversed",
        tickfont=dict(size=11)
    ),
    title=dict(
        text="Timeline Operacional - Zoom com Scroll",
        x=0.5,
        xanchor='center',
        font=dict(size=18)
    ),
    height=500 + 40 * len(linhas_unicas),
    margin=dict(l=120, r=40, t=60, b=50),
    hoverlabel=dict(font_size=11)
)

# HABILITAR INTERAÇÕES LEVES
config = {
    "scrollZoom": True,
    "displayModeBar": True,
    "responsive": True
}

# === EXIBIR ===
st.plotly_chart(fig, use_container_width=True, config=config)
