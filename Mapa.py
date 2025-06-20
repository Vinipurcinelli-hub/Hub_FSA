import streamlit as st
import pandas as pd
import pydeck as pdk

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Mapa das Localidades")
st.title("🗺️ Mapa das Localidades")
st.markdown("Cada ponto representa uma cidade da malha. As linhas conectam na ordem original da planilha.")

# --- Leitura do arquivo ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel("teste.xlsx")
        return df[["LOCALIDADE", "LAT", "LON"]].dropna()
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado para exibir.")
    st.stop()

# --- Ordena pela ordem do arquivo (mantida automaticamente)
df.reset_index(drop=True, inplace=True)

# --- Criar camada de pontos vermelhos ---
pontos_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position='[LON, LAT]',
    get_radius=7000,
    get_fill_color='[255, 0, 0, 160]',
    pickable=True,
)

# --- Criar conexões entre pontos consecutivos ---
conexoes = pd.DataFrame([
    {"source": [df["LON"][i], df["LAT"][i]], "target": [df["LON"][i+1], df["LAT"][i+1]]}
    for i in range(len(df) - 1)
])

linha_layer = pdk.Layer(
    "LineLayer",
    data=conexoes,
    get_source_position="source",
    get_target_position="target",
    get_color=[0, 100, 200],
    get_width=3,
)

# --- Visualização centralizada na rota ---
view_state = pdk.ViewState(
    latitude=df["LAT"].mean(),
    longitude=df["LON"].mean(),
    zoom=5,
)

# --- Mostrar o mapa ---
st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=view_state,
    layers=[pontos_layer, linha_layer],
    tooltip={"text": "{LOCALIDADE}"}
))

# --- Mostrar a tabela abaixo ---
with st.expander("🔍 Ver dados utilizados"):
    st.dataframe(df)
