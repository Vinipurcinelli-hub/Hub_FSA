import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# === CONFIGURAÇÃO STREAMLIT ===
st.set_page_config(layout="wide")
st.title("🕒 Timeline Operacional com Zoom e Dias da Semana")

# === CONSTANTES ===
CORES = {"GUANABARA": "royalblue", "ITAPEMIRIM": "gold", "HUB": "firebrick"}
ORDEM_DIAS = ["QUA", "QUI", "SEX", "SÁB", "DOM", "SEG", "TER"]


@st.cache_data
def load_data(path: str):
    """Carrega a planilha e prepara as colunas utilizadas no gráfico."""
    df = pd.read_excel(path)
    df["HORA PARTIDA"] = pd.to_datetime(df["HORA PARTIDA"])
    df["HORA CHEGADA"] = pd.to_datetime(df["HORA CHEGADA"])
    df["DURACAO_H"] = (
        df["HORA CHEGADA"] - df["HORA PARTIDA"]
    ).dt.total_seconds() / 3600
    df = df[df["DURACAO_H"] > 0].copy()

    dias_offset = (df["HORA PARTIDA"].dt.weekday - 2) % 7
    df["HORA_ABSOLUTA"] = (
        dias_offset * 24
        + df["HORA PARTIDA"].dt.hour
        + df["HORA PARTIDA"].dt.minute / 60
    )
    df["COR"] = df["EMPRESA"].map(CORES).fillna("gray")

    dia_col = "DIA SEMANA" if "DIA SEMANA" in df.columns else "DIA SEMANA PARTIDA"
    viagem_dia = df.groupby("VIAGEM")[dia_col].first().str.upper()
    viagens_ordenadas = sorted(
        viagem_dia.index, key=lambda v: ORDEM_DIAS.index(viagem_dia.loc[v])
    )
    df["VIAGEM"] = pd.Categorical(
        df["VIAGEM"], categories=viagens_ordenadas, ordered=True
    )
    df.sort_values("VIAGEM", inplace=True)
    return df, viagens_ordenadas


df, viagens_ordenadas = load_data("Planejamento operacional.xlsx")

# === GRÁFICO ===
fig = go.Figure()

# 1. Desenha os retângulos
for empresa, grupo in df.groupby("EMPRESA"):
    fig.add_trace(
        go.Bar(
            x=grupo["DURACAO_H"],
            y=grupo["VIAGEM"],
            base=grupo["HORA_ABSOLUTA"],
            orientation="h",
            marker=dict(
                color=CORES.get(empresa, "gray"), line=dict(color="black", width=1)
            ),
            name=empresa,
            legendgroup=empresa,
            width=0.35,
            customdata=grupo[["ORIGEM", "DESTINO", "HORA PARTIDA", "HORA CHEGADA"]],
            hovertemplate=(
                "<b>%{y}</b><br>" +
                "Origem: %{customdata[0]} → %{customdata[1]}<br>" +
                "Início: %{customdata[2]|%d/%m %H:%M}<br>" +
                "Fim: %{customdata[3]|%d/%m %H:%M}<br>" +
                "Duração: %{x:.1f}h"
        ),
            xaxis="x2",
        )
    )

# 2. Textos (origem e destino)
for empresa, grupo in df.groupby("EMPRESA"):
    fig.add_trace(go.Bar(
        x=grupo["DURACAO_H"],
        y=grupo["VIAGEM"],
        base=grupo["HORA_ABSOLUTA"],
        orientation="h",
        marker=dict(color='rgba(0,0,0,0)'),
        text=grupo["ORIGEM"],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(size=12, color="black", family="Arial Black"),
        showlegend=False,
        hoverinfo="skip",
        xaxis="x2"
    ))

    fig.add_trace(go.Bar(
        x=grupo["DURACAO_H"],
        y=grupo["VIAGEM"],
        base=grupo["HORA_ABSOLUTA"],
        orientation="h",
        marker=dict(color='rgba(0,0,0,0)'),
        text=grupo["DESTINO"],
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(size=12, color="black", family="Arial Black"),
        showlegend=False,
        hoverinfo="skip",
        xaxis="x2"
    ))

# === GRADE DE HORAS E DIAS ===
dias_semana = ["QUA", "QUI", "SEX", "SÁB", "DOM", "SEG", "TER", "QUA"]
ticks_dias = [i * 24 for i in range(8)]
x_ticks = list(range(0, 24 * 8 + 1))
x_labels = [str(h % 24) if h % 24 != 0 else "" for h in x_ticks]

# Delimitações entre os dias
for x in ticks_dias:
    fig.add_shape(
        type="line",
        x0=x,
        x1=x,
        y0=0,
        y1=1,
        xref="x2",
        yref="paper",
        line=dict(color="white", width=3),
        layer="below",
    )

# Fundo verde claro de 07:00 às 22:00
for dia in range(7):
    fig.add_shape(
        type="rect",
        x0=dia * 24 + 7,
        x1=dia * 24 + 22,
        y0=0,
        y1=1,
        xref="x2",
        yref="paper",
        fillcolor="rgba(144,238,144,0.2)",
        line=dict(width=0),
        layer="below"
    )

# Anotações dos dias da semana
anotacoes = []
for i, x in enumerate(ticks_dias):
    anotacoes.append(dict(
        x=x + 12,
        y=1.05,
        xref="x2",
        yref="paper",
        text=f"<b>{dias_semana[i]}</b>",
        showarrow=False,
        font=dict(size=14, color="white"),
        align="center"
    ))

# Layout final
fig.update_layout(
    annotations=anotacoes,
    barmode="stack",
    bargap=0.15,
    dragmode="pan",
    xaxis=dict(visible=False),
    xaxis2=dict(
        domain=[0.0, 1.0],
        anchor="y",
        tickmode="array",
        tickvals=x_ticks,
        ticktext=x_labels,
        showgrid=True,
        gridcolor="lightgray",
        griddash="dot",
        ticklen=3,
        tickfont=dict(size=9),
        ticks="outside",
        title="Horário do Dia",
        range=[0, 24 * 8],
    ),
    yaxis=dict(
        title="VIAGEM",
        autorange="reversed",
        tickfont=dict(size=11),
        categoryorder="array",
        categoryarray=viagens_ordenadas
    ),
    height=500 + 50 * len(viagens_ordenadas),
    margin=dict(l=100, r=40, t=100, b=80),
    title=dict(
        text="Timeline Operacional – Dias da Semana com Zoom Inteligente",
        x=0.5,
        font=dict(size=18)
    ),
    hoverlabel=dict(font_size=11)
)

# Exibição
config = {
    "scrollZoom": True,
    "displayModeBar": True,
    "responsive": True
}
st.plotly_chart(fig, use_container_width=True, config=config)
