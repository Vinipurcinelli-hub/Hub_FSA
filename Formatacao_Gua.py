import pandas as pd

# Arquivos de entrada
arquivo_rotas = "QT Guanabara - Maio de 2025.xlsx"
arquivo_coordenadas = "Coordenadas_gua.xlsx"

# Leitura das planilhas
rotas = pd.read_excel(arquivo_rotas)
coordenadas = pd.read_excel(arquivo_coordenadas)

# Normaliza texto para facilitar comparacoes
rotas['ORIGEM'] = rotas['ORIGEM'].str.strip()
rotas['DESTINO'] = rotas['DESTINO'].str.strip()
rotas['SECOES DA LINHA'] = rotas['SECOES DA LINHA'].str.strip()
coordenadas['CIDADE (UF)'] = coordenadas['CIDADE (UF)'].str.strip()

resultado = []

# Agrupa pelas chaves solicitadas
for (prefixo, desc), grupo in rotas.groupby(['PREFIXO', 'DESCRICAO DA LINHA']):
    partes_desc = [p.strip() for p in desc.split(' - ')[:2]]
    origem_desc, destino_desc = partes_desc[0], partes_desc[1]

    # Extrai cada origem em ordem de aparicao na coluna "SECOES DA LINHA"
    cidades_seq = (
        grupo['SECOES DA LINHA']
        .str.extract(r'^(.*?) -')[0]
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
            'DESCRICAO DA LINHA': desc,
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
