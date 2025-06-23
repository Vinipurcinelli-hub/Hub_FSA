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
rotas['DESCRICAO DA LINHA'] = rotas['DESCRICAO DA LINHA'].apply(
    lambda x: ' - '.join(format_city(p) for p in x.split(' - '))
)
coordenadas['CIDADE (UF)'] = coordenadas['CIDADE (UF)'].apply(format_city)

resultado = []

# Agrupa pelas chaves solicitadas
for (prefixo, desc), grupo in rotas.groupby(['PREFIXO', 'DESCRICAO DA LINHA']):
    desc_formatado = format_city(desc)
    partes_desc = [p.strip() for p in desc_formatado.split(' - ')[:2]]
    if len(partes_desc) < 2:
        continue
    origem_desc, destino_desc = partes_desc

    # Mantem a ordem das cidades conforme aparecem
    grupo = grupo.sort_index()
    cidades_seq = []
    visitados = set()

    if origem_desc not in visitados:
        cidades_seq.append(origem_desc)
        visitados.add(origem_desc)

    for idx, row in grupo.iterrows():
        cidade_origem = row['ORIGEM']
        if cidade_origem not in visitados:
            cidades_seq.append(cidade_origem)
            visitados.add(cidade_origem)
        cidade_dest = row['DESTINO']
        if not (idx == grupo.index.min() and cidade_dest == destino_desc and cidade_origem == origem_desc):
            if cidade_dest not in visitados:
                cidades_seq.append(cidade_dest)
                visitados.add(cidade_dest)

    if destino_desc not in visitados:
        cidades_seq.append(destino_desc)

    sentido = "IDA" if cidades_seq[0] == origem_desc else "VOLTA"

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