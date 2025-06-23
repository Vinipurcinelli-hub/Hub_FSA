import streamlit as st
import pandas as pd
import pydeck as pdk

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Mapa do projeto")
st.title("🗺️ Projeto Operação integrada - Nova Itapemirim & Guanabara")

# --- Função para carregar os dados ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel("esqueleto.xlsx")
        df = df.dropna(subset=["LAT", "LON", "SEQUENCIA"])
        df["SEQUENCIA"] = pd.to_numeric(df["SEQUENCIA"], errors="coerce")
        df["LAT"] = df["LAT"].astype(float)
        df["LON"] = df["LON"].astype(float)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado válido para exibir.")
    st.stop()

# --- Ordenar os dados pela sequência das cidades dentro de cada linha ---
df = df.sort_values(by=["PREFIXO SIGMA", "NOME DA LINHA", "SERVICO", "TIPO_VEICULO", "FREQUENCIA", "SEQUENCIA"])

# --- Criar DataFrame seguro apenas com coordenadas ---
df_pontos = df[["LAT", "LON"]].copy()
df_pontos = df_pontos.dropna()
df_pontos["lat"] = df_pontos["LAT"].astype(float)
df_pontos["lon"] = df_pontos["LON"].astype(float)

# --- Verificar se há valores inválidos ---
if df_pontos["lat"].isnull().any() or df_pontos["lon"].isnull().any():
    st.error("Erro: coordenadas inválidas nos pontos.")
    st.stop()

# --- Criar camada de pontos vermelhos ---
pontos_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_pontos[["lat", "lon"]],
    get_position='[lon, lat]',
    get_fill_color='[255, 0, 0, 160]',
    pickable=False,
    radius_min_pixels=4,
    radius_max_pixels=30
)

# --- Gerar conexões entre localidades da mesma linha ---
conexoes = []
grupos = df.groupby(['PREFIXO SIGMA', 'NOME DA LINHA', 'SERVICO', 'TIPO_VEICULO', 'FREQUENCIA'])

for chave, grupo in grupos:
    grupo_ordenado = grupo.sort_values(by="SEQUENCIA")
    for i in range(len(grupo_ordenado) - 1):
        origem = grupo_ordenado.iloc[i]
        destino = grupo_ordenado.iloc[i + 1]
        conexoes.append({
            "source": [float(origem["LON"]), float(origem["LAT"])],
            "target": [float(destino["LON"]), float(destino["LAT"])]
        })

# --- Criar camada de linhas de conexão ---
linha_layer = pdk.Layer(
    "LineLayer",
    data=pd.DataFrame(conexoes),
    get_source_position="source",
    get_target_position="target",
    get_color=[0, 100, 200],
    get_width=3,
)

linha_horizontal = pdk.Layer(
    "PathLayer",
    data=pd.DataFrame({
        "path": [[[ -180, -12.2292842525 ], [ 180, -12.2292842525 ]]]
    }),
    get_path="path",
    # A cor branca não fica visível com o tema claro do Streamlit.
    # Usamos preto para destacar a linha horizontal no modo Light.
    get_color=[0, 0, 0],
    get_width=20,         # <--- aumente aqui para engrossar
    width_scale=1,
    width_min_pixels=2,
    width_max_pixels=10,
    opacity=0.6,
    dash_size=4,
    gap_size=2,
)

# --- Destaque do HUB SALA VIP ---
HUB_LAT = -13.4884524
HUB_LON = -39.1411053
OFFSET = 0.05  # tamanho do retângulo em graus

retangulo_data = pd.DataFrame({
    "coordinates": [[
        [HUB_LON - OFFSET, HUB_LAT - OFFSET],
        [HUB_LON - OFFSET, HUB_LAT + OFFSET],
        [HUB_LON + OFFSET, HUB_LAT + OFFSET],
        [HUB_LON + OFFSET, HUB_LAT - OFFSET],
    ]]
})

retangulo_layer = pdk.Layer(
    "PolygonLayer",
    data=retangulo_data,
    get_polygon="coordinates",
    get_fill_color=[255, 255, 255, 0],  # sem preenchimento
    get_line_color=[0, 0, 0],
    get_line_width=4,
)

titulo_layer = pdk.Layer(
    "TextLayer",
    data=pd.DataFrame({
        "coordinates": [[HUB_LON, HUB_LAT]],
        "text": ["HUB SALA VIP\nFEIRA DE SANTANA"],
    }),
    get_position="coordinates",
    get_text="text",
    get_color=[0, 0, 0],
    get_size=24,
    get_text_anchor="'middle'",
    get_alignment_baseline="'top'",
)

# --- View inicial centralizada ---
view_state = pdk.ViewState(
    latitude=df["LAT"].mean(),
    longitude=df["LON"].mean(),
    zoom=5,
)

# --- Mostrar o mapa ---
st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=view_state,
    layers=[
        pontos_layer,
        linha_layer,
        linha_horizontal,
        retangulo_layer,
        titulo_layer,
    ]
))

# --- Mostrar os dados ---
with st.expander("🔍 Ver dados utilizados"):
    st.dataframe(df)
