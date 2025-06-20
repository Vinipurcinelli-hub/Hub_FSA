import pandas as pd
from datetime import datetime

# Caminhos dos arquivos
arquivo_malha = "18 06 2025 - Malha.xlsx"
arquivo_linhas_ativas = "linhas_FSA.xlsx"

# Leitura das planilhas
df_malha = pd.read_excel(arquivo_malha, sheet_name="Minha Planilha")
df_linhas = pd.read_excel(arquivo_linhas_ativas, sheet_name="linhas_FSA")

# Garante que as colunas de comparação sejam do mesmo tipo (texto)
df_malha["CODIGO_LINHA"] = df_malha["CODIGO_LINHA"].astype(str).str.strip()
df_linhas["PREFIXO SIGMA"] = df_linhas["PREFIXO SIGMA"].astype(str).str.strip()
df_linhas["NOME DA LINHA"] = df_linhas["NOME DA LINHA"].astype(str).str.strip()

# Remove duplicatas
df_linhas_unico = df_linhas.drop_duplicates(subset=["PREFIXO SIGMA"])

# Merge somente com os dados de linhas ativas (filtro com inner join)
df_completo = df_malha.merge(
    df_linhas_unico[["PREFIXO SIGMA", "NOME DA LINHA"]],
    how="inner",  # <- aqui está a correção principal
    left_on="CODIGO_LINHA",
    right_on="PREFIXO SIGMA"
)

# Remove a coluna de chave duplicada
df_completo.drop(columns=["PREFIXO SIGMA"], inplace=True)

# Reorganiza para que "NOME DA LINHA" fique à direita de "CODIGO_LINHA"
colunas = df_completo.columns.tolist()
colunas.remove("NOME DA LINHA")
idx = colunas.index("CODIGO_LINHA")
colunas.insert(idx + 1, "NOME DA LINHA")
df_completo = df_completo[colunas]

# Renomeia colunas
df_completo.rename(columns={"CODIGO_LINHA": "PREFIXO SIGMA"}, inplace=True)
df_completo.rename(columns={"HORA_PARTIDA": "HORARIO"}, inplace=True)

# Remove coluna indesejada
if "NOME" in df_completo.columns:
    df_completo.drop(columns=["NOME"], inplace=True)

# Formatação da hora
def formatar_hora(valor):
    if pd.notna(valor) and str(valor).replace(":", "").isdigit():
        valor = str(int(valor)).zfill(4)
        return f"{valor[:2]}:{valor[2:]}"
    return valor

df_completo['HORARIO'] = df_completo["HORARIO"].apply(formatar_hora)

# Localidade em maiúsculas
df_completo['LOCALIDADE'] = df_completo['LOCALIDADE'].str.upper()

# Tradução dos dias
traduzir_dia = {
    "DIA ATUAL": "D+0",
    "DIA +1": "D+1",
    "DIA +2": "D+2",
    "DIA +3": "D+3"
}
df_completo['DIA_PARTIDA'] = df_completo['DIA_PARTIDA'].map(traduzir_dia)

# --- Lê a base de coordenadas ---
df_coords = pd.read_excel("Coordenadas.xlsx")

# Tenta converter para float; se der erro (por causa da vírgula), substitui e converte de novo
for col in ["LAT", "LON"]:
    try:
        df_coords[col] = pd.to_numeric(df_coords[col], errors="raise")
    except:
        df_coords[col] = df_coords[col].astype(str).str.replace(",", ".").astype(float)

# Garante que os nomes estejam no mesmo formato
df_coords["CIDADE"] = df_coords["CIDADE"].str.upper().str.strip()
df_completo["LOCALIDADE"] = df_completo["LOCALIDADE"].str.upper().str.strip()

# --- Filtra apenas localidades que existem em Coordenadas.xlsx ---
df_completo = df_completo[df_completo["LOCALIDADE"].isin(df_coords["CIDADE"])].copy()

# --- Adiciona LAT e LON com base na correspondência LOCALIDADE ↔ CIDADE ---
df_completo = df_completo.merge(
    df_coords[["CIDADE", "LAT", "LON"]],
    how="left",
    left_on="LOCALIDADE",
    right_on="CIDADE"
)

# Remove a coluna CIDADE (duplicada do merge)
df_completo.drop(columns=["CIDADE"], inplace=True)

# Ordenação
df_completo = df_completo.sort_values(by=['SERVICO', 'FREQUENCIA', 'DIA_PARTIDA', 'HORARIO'])

def extrair_origem_destino(nome_linha):
    partes = nome_linha.split(" - ")
    if len(partes) >= 2:
        origem = partes[0].strip().split("(")[0].strip()
        destino = partes[1].strip().split("(")[0].strip()
        return origem.upper(), destino.upper()
    return None, None

# Inicializa a coluna SENTIDO
df_completo["SENTIDO"] = "erro"

# Agrupamento conforme solicitado
grupos = df_completo.groupby(['PREFIXO SIGMA', 'NOME DA LINHA', 'SERVICO', 'TIPO_VEICULO', 'FREQUENCIA'])

# Lista para armazenar os blocos
df_processado = []

for _, grupo in grupos:
    grupo_ordenado = grupo.copy().sort_values(by=['SERVICO', 'FREQUENCIA', 'DIA_PARTIDA', 'HORARIO'])

    origem, destino = extrair_origem_destino(grupo_ordenado['NOME DA LINHA'].iloc[0])
    primeira_localidade = grupo_ordenado['LOCALIDADE'].iloc[0].upper().strip()
    ultima_localidade = grupo_ordenado['LOCALIDADE'].iloc[-1].upper().strip()

    if origem and primeira_localidade == origem:
        sentido = "IDA"
    elif destino and ultima_localidade == destino:
        sentido = "IDA"
    elif destino and primeira_localidade == destino:
        sentido = "VOLTA"
    else:
        sentido = "erro"

    grupo_ordenado["SENTIDO"] = sentido

    # 🔢 Adiciona coluna de sequência (1 até N por bloco)
    grupo_ordenado["SEQUENCIA"] = range(1, len(grupo_ordenado) + 1)

    df_processado.append(grupo_ordenado)

# Concatena tudo novamente
df_completo = pd.concat(df_processado, ignore_index=True)

# Exporta para CSV
df_completo.to_csv("Malha_Formatada.csv", index=False, sep=';', encoding='utf-8-sig', decimal=',')