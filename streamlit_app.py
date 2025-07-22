import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# === CONFIGURAÇÃO STREAMLIT ===
st.set_page_config(layout="wide")
st.title("🕒 Timeline Operacional - HUB FSA - ITAPEMIRIM + GUANABARA")

# === CONSTANTES ===
CORES = {"GUANABARA": "royalblue", "ITAPEMIRIM": "gold", "HUB": "firebrick"}
ORDEM_DIAS = ["QUA", "QUI", "SEX", "SÁB", "DOM", "SEG", "TER"]
LIMIAR_TEXTO = 8  # horas

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

    # Calcula a diferença, em horas, entre a primeira quarta-feira e cada
    # horário de partida para manter a continuidade mesmo após a troca de semana
    primeira_data = df["HORA PARTIDA"].min().normalize()
    dias_ate_quarta = (primeira_data.weekday() - 2) % 7
    quarta_inicial = primeira_data - pd.Timedelta(days=dias_ate_quarta)
    df["HORA_ABSOLUTA"] = (
        (df["HORA PARTIDA"] - quarta_inicial).dt.total_seconds() / 3600
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

# Considera apenas os primeiros 10 dias (de quarta a sexta da semana seguinte)


# Divide os blocos que ultrapassam o final da terça-feira (168h)
LIMITE_SEMANA = 168  # 7 dias * 24 horas
df_quebrado = []

for _, row in df.iterrows():
    hora_ini = row["HORA_ABSOLUTA"]
    dur = row["DURACAO_H"]
    hora_fim = hora_ini + dur

    if hora_ini < LIMITE_SEMANA and hora_fim <= LIMITE_SEMANA:
        # Bloco totalmente dentro da semana
        df_quebrado.append(row)
        row["BLOCO_QUEBRADO"] = "completo"


    elif hora_ini < LIMITE_SEMANA and hora_fim > LIMITE_SEMANA:
        # Bloco que cruza terça — quebrar em dois
        parte1 = row.copy()
        parte1["DURACAO_H"] = LIMITE_SEMANA - hora_ini
        parte1["BLOCO_QUEBRADO"] = "final"
        df_quebrado.append(parte1)
        
        parte2 = row.copy()
        parte2["HORA_ABSOLUTA"] = 0
        parte2["DURACAO_H"] = hora_fim - LIMITE_SEMANA
        parte2["BLOCO_QUEBRADO"] = "inicio"
        df_quebrado.append(parte2)

    elif hora_ini >= LIMITE_SEMANA:
        # Bloco que começa após terça — realocar na esquerda
        parte = row.copy()
        parte["HORA_ABSOLUTA"] = hora_ini - LIMITE_SEMANA
        df_quebrado.append(parte)

df = pd.DataFrame(df_quebrado)





# Todos os blocos são tratados de maneira única
df["PARTE"] = 0

# Define qual coluna de dia da semana usar
dia_col = "DIA SEMANA" if "DIA SEMANA" in df.columns else "DIA SEMANA PARTIDA"
# Insere quebra de linha após ' - "', sem considerar ')'
df["VIAGEM"] = df["VIAGEM"].astype(str).str.replace(' - "', '<br>"', regex=False)

# Recalcula os ordenamentos com os nomes já formatados


# Agrupar por viagem para obter o dia da semana e o horário de partida
# Converte a hora para valor decimal (ex: 13:30 → 13.5)
df["HORA_VIAGEM_DECIMAL"] = df["HORA VIAGEM"].apply(
    lambda x: x.hour + x.minute / 60 if pd.notnull(x) else None
)

# Agrupa por VIAGEM e extrai o dia e hora decimal
viagem_info = df.groupby("VIAGEM").agg({
    dia_col: lambda x: x.iloc[0].upper(),
    "HORA_VIAGEM_DECIMAL": "first"
})

# Ordena por dia e hora
viagem_info["ORD_DIA"] = viagem_info[dia_col].apply(lambda d: ORDEM_DIAS.index(d))
viagem_info = viagem_info.sort_values(["ORD_DIA", "HORA_VIAGEM_DECIMAL"])

# Gera a nova ordenação
viagens_ordenadas = viagem_info.index.tolist()




df["VIAGEM"] = pd.Categorical(df["VIAGEM"], categories=viagens_ordenadas, ordered=True)

# === GRÁFICO ===
fig = go.Figure()

# 0. Camada de fundo levemente opaca para bloquear a grade atrás dos blocos
for empresa, grupo in df.groupby("EMPRESA"):
    fig.add_trace(
        go.Bar(
            x=grupo["DURACAO_H"],
            y=grupo["VIAGEM"],
            base=grupo["HORA_ABSOLUTA"],
            orientation="h",
            marker=dict(
                color="rgba(0,0,0,0.4)",  # tom escuro translúcido — pode ajustar
                line=dict(width=0)
            ),
            width=0.50,  # levemente maior que os blocos reais
            showlegend=False,
            hoverinfo="skip",
            xaxis="x2"
        )
    )


# 1. Desenha os retângulos
for empresa, grupo in df.groupby("EMPRESA"):
    fig.add_trace(
        go.Bar(
            x=grupo["DURACAO_H"],
            y=grupo["VIAGEM"],
            base=grupo["HORA_ABSOLUTA"],
            orientation="h",
            marker=dict(
                color=CORES.get(empresa, "gray"),
                line=dict(
                    color="black" if empresa != "HUB" else "rgba(0,0,0,0)",
                    width=1 if empresa != "HUB" else 0
                )
            ),
            name=empresa,
            legendgroup=empresa,
            width=0.35 if empresa != "HUB" else 1,
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

# 2. Textos para dentro dos blocos — com exceção "SPO" para blocos curtos
textos_esquerda = []
textos_direita = []

for idx, row in df.iterrows():
    dur = row["DURACAO_H"]
    sentido = str(row.get("SENTIDO", "")).upper().strip()
    tipo_quebra = row.get("BLOCO_QUEBRADO", "completo")

    if dur < LIMIAR_TEXTO:
        if sentido == "IDA":
            textos_esquerda.append("")
            textos_direita.append(row["DESTINO"])
        elif sentido == "VOLTA":
            textos_esquerda.append(row["ORIGEM"])
            textos_direita.append("")
        else:
            textos_esquerda.append("")
            textos_direita.append("")
    else:
        if tipo_quebra == "inicio":
            textos_esquerda.append("")
            textos_direita.append(row["DESTINO"])
        elif tipo_quebra == "final":
            textos_esquerda.append(row["ORIGEM"])
            textos_direita.append("")
        else:
            textos_esquerda.append(row["ORIGEM"])
            textos_direita.append(row["DESTINO"])


# ORIGEM (esquerda) – só aparece se for >= 8h
fig.add_trace(
    go.Bar(
        x=df["DURACAO_H"],
        y=df["VIAGEM"],
        base=df["HORA_ABSOLUTA"],
        orientation="h",
        marker=dict(color="rgba(0,0,0,0)"),
        text=textos_esquerda,
        textposition="inside",
        insidetextanchor="start",
        textangle=0,  # mantém na horizontal
        textfont=dict(size=12, color="black", family="Arial Black"),
        showlegend=False,
        hoverinfo="skip",
        xaxis="x2",
    )
)

# DESTINO (direita) – sempre "SPO" em blocos curtos
fig.add_trace(
    go.Bar(
        x=df["DURACAO_H"],
        y=df["VIAGEM"],
        base=df["HORA_ABSOLUTA"],
        orientation="h",
        marker=dict(color="rgba(0,0,0,0)"),
        text=textos_direita,
        textposition="inside",
        insidetextanchor="end",
        textangle=0,
        textfont=dict(size=12, color="black", family="Arial Black"),
        showlegend=False,
        hoverinfo="skip",
        xaxis="x2",
    )
)

# === GRADE DE HORAS E DIAS ===
x_ticks = list(range(0, 24 * 7 + 1))
dias_semana = ["QUA", "QUI", "SEX", "SÁB", "DOM", "SEG", "TER"]

ticks_dias = [i * 24 for i in range(7)]
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

# Fundo verde claro de 07:00 às 22:00 para cada um dos dez dias
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
        y=1.015,
        xref="x2",
        yref="paper",
        text=f"<b>{dias_semana[i]}</b>",
        showarrow=False,
        font=dict(size=14, color="white"),
        align="center"
    ))

# Legenda para o período de operação do HUB
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(size=10, color="rgba(144,238,144,0.2)", symbol="square"),
        showlegend=True,
        name="HUB - FSA<br>(07:00 às 22:00)",
        hoverinfo="skip",
        legendgroup="CATEGORIAS",
        xaxis="x2"
    )
)

LEGENDA_OBS = {
    1: "1 - INTEGRADO - FREQ. MÍNIMA",
    2: "2 - INTEGRADO + HUB GUANABARA",
    3: "3 - INTERCONEXÕES + HUB GUANABARA",
    4: "4 - FREQ. MÍNIMA"
}

# Legenda visual para os códigos de OBS (1 a 4)
for cod in sorted(LEGENDA_OBS.keys(), reverse=True):
    texto = LEGENDA_OBS[cod]
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color="white", symbol="circle"),  # cor neutra
            showlegend=True,
            name=texto,
            hoverinfo="skip",
            legendgroup="CATEGORIAS",
            xaxis="x2"
        )
    )

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
        range=[0, 24 * 7],
    ),
    yaxis=dict(
        title="VIAGEM",
        autorange="reversed",
        tickfont=dict(size=11),
        categoryorder="array",
        categoryarray=viagens_ordenadas
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.12,
        xanchor="left",
        x=0,
        font=dict(size=13),
        traceorder="normal",  # força a sequência correta
    ),
    height=500 + 30 * len(viagens_ordenadas),
    margin=dict(l=10, r=10, t=10, b=60),
    hoverlabel=dict(font_size=11)
)


# Exibição
config = {
    "scrollZoom": True,
    "displayModeBar": True,
    "responsive": True
}
st.plotly_chart(fig, use_container_width=True, config=config)
