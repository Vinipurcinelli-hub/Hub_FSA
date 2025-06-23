import pandas as pd
import re

# Arquivos de entrada
arquivo_rotas = "QT Guanabara - Maio de 2025.xlsx"
arquivo_coordenadas = "Coordenadas_gua.xlsx"

# Leitura das planilhas
rotas = pd.read_excel(arquivo_rotas)
coordenadas = pd.read_excel(arquivo_coordenadas)

# Normaliza texto para facilitar comparacoes
def format_city(cidade: str) -> str:
    """Normaliza a cidade colocando espaco antes do parenteses."""
    if pd.isna(cidade):
        return cidade
    cidade = cidade.strip()
    return re.sub(r"\s*\((\w{2})\)", r" (\1)", cidade)

rotas['ORIGEM'] = rotas['ORIGEM'].apply(format_city)
rotas['DESTINO'] = rotas['DESTINO'].apply(format_city)
rotas['SECOES DA LINHA'] = rotas['SECOES DA LINHA'].apply(
    lambda s: ' - '.join(format_city(p.strip()) for p in s.split(' - '))
)
coordenadas['CIDADE (UF)'] = coordenadas['CIDADE (UF)'].apply(format_city)

resultado = []

# Agrupa pelas chaves solicitadas
for (prefixo, desc), grupo in rotas.groupby(['PREFIXO', 'DESCRICAO DA LINHA']):
    desc_formatado = format_city(desc)
    partes_desc = [p.strip() for p in desc_formatado.split(' - ')[:2]]
    if len(partes_desc) < 2:
        continue
    origem_desc, destino_desc = partes_desc[0], partes_desc[1]

    # Extrai cada origem em ordem de aparicao na coluna "SECOES DA LINHA"
    cidades_seq = (
        grupo['SECOES DA LINHA']
        .str.extract(r'^(.*?) -')[0]
        .apply(format_city)
        .drop_duplicates()
        .tolist()
    )

    # Garante que a cidade final apareca na sequencia
    if destino_desc not in cidades_seq:
        cidades_seq.append(destino_desc)

    primeira_cidade = cidades_seq[0]
    ultima_cidade = cidades_seq[-1]

    # Determina o sentido
    if primeira_cidade == origem_desc:
        sentido = "IDA"
    elif primeira_cidade == destino_desc:
        sentido = "VOLTA"
    elif ultima_cidade == destino_desc:
        sentido = "IDA"
    else:
        sentido = "IDA"

    # Cria linhas para cada cidade da sequencia
    for sequencia, cidade in enumerate(cidades_seq, start=1):
        coord = coordenadas[coordenadas['CIDADE (UF)'] == cidade]
        lat = coord['LAT'].iloc[0] if not coord.empty else None
        lon = coord['LON'].iloc[0] if not coord.empty else None
        resultado.append({
            'PREFIXO': prefixo,
            'DESCRICAO DA LINHA': desc_formatado,
            'CIDADES': cidade,
            'LAT': lat,
            'LON': lon,
            'SENTIDO': sentido,
            'SEQUENCIA': sequencia
        })

# Concatena todos os blocos
df_resultado = pd.DataFrame(resultado)

# Exporta para Excel
df_resultado.to_excel('Rotas_Guanabara_Formatadas.xlsx', index=False)

