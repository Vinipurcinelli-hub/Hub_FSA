import pandas as pd
import re
from typing import Optional, Tuple

# Arquivos de entrada
ARQUIVO_ROTAS = "QT Guanabara - Maio de 2025.xlsx"
ARQUIVO_COORD = "Coordenadas_gua.xlsx"

rotas = pd.read_excel(ARQUIVO_ROTAS)
coordenadas = pd.read_excel(ARQUIVO_COORD)


def format_city(cidade: str) -> str:
    """Normaliza cidade para o formato 'NOME (UF)'"""
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


def get_coord(cidade: str) -> Optional[Tuple[float, float]]:
    linha = coordenadas[coordenadas['CIDADE (UF)'] == cidade]
    if linha.empty:
        return None
    return linha['LAT'].iloc[0], linha['LON'].iloc[0]


def param_along(orig: Tuple[float, float], dest: Tuple[float, float], pt: Optional[Tuple[float, float]]) -> float:
    """Calcula a projecao de pt no vetor origem->destino."""
    if pt is None or orig is None or dest is None:
        return float('inf')
    ox, oy = orig
    dx, dy = dest
    px, py = pt
    vx = dx - ox
    vy = dy - oy
    wx = px - ox
    wy = py - oy
    denom = vx * vx + vy * vy
    if denom == 0:
        return float('inf')
    return (wx * vx + wy * vy) / denom


resultado = []
for (prefixo, desc), grupo in rotas.groupby(['PREFIXO', 'DESCRICAO DA LINHA']):
    desc_fmt = format_city(desc)
    partes = [p.strip() for p in desc_fmt.split(' - ')[:2]]
    if len(partes) < 2:
        continue
    origem_desc, destino_desc = partes

    cidades = pd.unique(grupo[['ORIGEM', 'DESTINO']].values.ravel('K'))
    cidades = [format_city(c) for c in cidades if pd.notna(c)]

    if origem_desc not in cidades:
        cidades.insert(0, origem_desc)
    if destino_desc not in cidades:
        cidades.append(destino_desc)

    # Remove duplicatas preservando ordem
    cidades_unique = []
    for c in cidades:
        if c not in cidades_unique:
            cidades_unique.append(c)

    coord_origem = get_coord(origem_desc)
    coord_destino = get_coord(destino_desc)

    cidades_ord = sorted(
        enumerate(cidades_unique),
        key=lambda x: param_along(coord_origem, coord_destino, get_coord(x[1]))
    )
    cidades_ord = [c for _, c in cidades_ord]

    sentido = 'IDA' if cidades_ord and cidades_ord[0] == origem_desc else 'VOLTA'

    for seq, cidade in enumerate(cidades_ord, start=1):
        lat_lon = get_coord(cidade)
        lat = lat_lon[0] if lat_lon else None
        lon = lat_lon[1] if lat_lon else None
        resultado.append({
            'PREFIXO': prefixo,
            'DESCRICAO DA LINHA': desc_fmt,
            'CIDADES': cidade,
            'LAT': lat,
            'LON': lon,
            'SENTIDO': sentido,
            'SEQUENCIA': seq
        })


df_resultado = pd.DataFrame(resultado)
df_resultado.to_excel('Rotas_Guanabara_Formatadas.xlsx', index=False)
