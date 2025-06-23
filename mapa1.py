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
    get_fill_color='[0, 0, 0, 160]',
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
    get_color=[254, 221, 49],
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

# --- View inicial centralizada ---
view_state = pdk.ViewState(
    latitude=df["LAT"].mean(),
    longitude=df["LON"].mean(),
    zoom=5,
)

# --- Mostrar mapa e lista de linhas da Itapemirim lado a lado ---
col_mapa_itap, col_tabela_itap = st.columns([3, 1])

with col_mapa_itap:
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=[
                pontos_layer,
                linha_layer,
                linha_horizontal
            ]
        ),
        use_container_width=True,
        height=800,
    )

with col_tabela_itap:
    linhas_itap = (
        df["DESCRICAO DA LINHA"] if "DESCRICAO DA LINHA" in df.columns
        else df["NOME DA LINHA"]
    )
    linhas_itap_df = pd.DataFrame(sorted(linhas_itap.unique()), columns=["LINHA"])
    st.dataframe(linhas_itap_df, hide_index=True)

# --- Mostrar os dados ---
with st.expander("🔍 Ver dados utilizados"):
    st.dataframe(df)

# --- Carregar dados da Guanabara ---
@st.cache_data
def carregar_dados_gua():
    try:
        df_g = pd.read_excel("Linhas_selecionadas_Gua.xlsx")
        df_g = df_g.dropna(subset=["LAT", "LON", "SEQUENCIA"])
        df_g["SEQUENCIA"] = pd.to_numeric(df_g["SEQUENCIA"], errors="coerce")
        df_g["LAT"] = df_g["LAT"].astype(float)
        df_g["LON"] = df_g["LON"].astype(float)
        return df_g
    except Exception as e:
        st.error(f"Erro ao carregar arquivo da Guanabara: {e}")
        return pd.DataFrame()

df_gua = carregar_dados_gua()

if df_gua.empty:
    st.warning("Nenhum dado válido para exibir para a Guanabara.")
    st.stop()

# --- Ordenar os dados pela sequência das cidades dentro de cada linha ---
df_gua = df_gua.sort_values(by=["PREFIXO", "DESCRICAO DA LINHA", "SEQUENCIA"])

# --- Filtro de linhas ---
linhas_unicas = sorted(df_gua["DESCRICAO DA LINHA"].unique())
selecionadas = st.multiselect(
    "Selecione as linhas da Guanabara",
    options=linhas_unicas,
    default=linhas_unicas,
)

if not selecionadas:
    st.warning("Selecione ao menos uma linha para visualizar as conexões da Guanabara.")
    st.stop()

df_gua_filtrado = df_gua[df_gua["DESCRICAO DA LINHA"].isin(selecionadas)]

# --- Criar DataFrame seguro apenas com coordenadas ---
df_gua_pontos = df_gua_filtrado[["LAT", "LON"]].copy()
df_gua_pontos = df_gua_pontos.dropna()
df_gua_pontos["lat"] = df_gua_pontos["LAT"].astype(float)
df_gua_pontos["lon"] = df_gua_pontos["LON"].astype(float)

# --- Verificar se há valores inválidos ---
if df_gua_pontos["lat"].isnull().any() or df_gua_pontos["lon"].isnull().any():
    st.error("Erro: coordenadas inválidas nos pontos da Guanabara.")
    st.stop()

# --- Criar camada de pontos pretos ---
pontos_gua_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_gua_pontos[["lat", "lon"]],
    get_position='[lon, lat]',
    get_fill_color='[0, 0, 0, 160]',
    pickable=False,
    radius_min_pixels=4,
    radius_max_pixels=30
)

# --- Gerar conexões entre localidades da mesma linha ---
conexoes_gua = []
grupos_gua = df_gua_filtrado.groupby(["PREFIXO", "DESCRICAO DA LINHA"])

for _, grupo in grupos_gua:
    grupo_ordenado = grupo.sort_values(by="SEQUENCIA")
    grupo_ordenado["NEXT_LAT"] = grupo_ordenado["LAT"].shift(-1)
    grupo_ordenado["NEXT_LON"] = grupo_ordenado["LON"].shift(-1)
    for _, row in grupo_ordenado[:-1].iterrows():
        if pd.notna(row["NEXT_LAT"]) and pd.notna(row["NEXT_LON"]):
            conexoes_gua.append({
                "source": [float(row["LON"]), float(row["LAT"])],
                "target": [float(row["NEXT_LON"]), float(row["NEXT_LAT"])]
            })

# --- Criar camada de linhas de conexão ---
linha_gua_layer = pdk.Layer(
    "LineLayer",
    data=pd.DataFrame(conexoes_gua),
    get_source_position="source",
    get_target_position="target",
    get_color=[0, 0, 139],
    get_width=3,
)

linha_horizontal_gua = pdk.Layer(
    "PathLayer",
    data=pd.DataFrame({
        "path": [[[-180, -12.2292842525], [180, -12.2292842525]]]
    }),
    get_path="path",
    get_color=[0, 0, 0],
    get_width=20,
    width_scale=1,
    width_min_pixels=2,
    width_max_pixels=10,
    opacity=0.6,
    dash_size=4,
    gap_size=2,
)

# --- View inicial centralizada ---
view_state_gua = pdk.ViewState(
    latitude=df_gua_filtrado["LAT"].mean(),
    longitude=df_gua_filtrado["LON"].mean(),
    zoom=5,
)

# --- Mostrar o mapa da Guanabara ---

# --- Mostrar mapa e lista de linhas da Guanabara lado a lado ---
col_mapa_gua, col_tabela_gua = st.columns([3, 1])

with col_mapa_gua:
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=view_state_gua,
            layers=[
                pontos_gua_layer,
                linha_gua_layer,
                linha_horizontal_gua
            ]
        ),
        use_container_width=True,
        height=800,
    )

with col_tabela_gua:
    linhas_gua_df = pd.DataFrame(
        sorted(df_gua_filtrado["DESCRICAO DA LINHA"].unique()),
        columns=["LINHA"]
    )
    st.dataframe(linhas_gua_df, hide_index=True)

# --- Mostrar os dados da Guanabara ---
with st.expander("🔍 Ver dados utilizados - Guanabara"):
    st.dataframe(df_gua_filtrado)
