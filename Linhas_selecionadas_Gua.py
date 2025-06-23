import pandas as pd

LIMITE_LATITUDE = -12.2292842525
ARQUIVO_ORIGEM = "Rotas_Guanabara_Formatadas.xlsx"
ARQUIVO_DESTINO = "Linhas_selecionadas_Gua.xlsx"

def selecionar_rotas_que_cruzam(arquivo_origem: str = ARQUIVO_ORIGEM,
                                limite: float = LIMITE_LATITUDE) -> pd.DataFrame:
    """Retorna somente os grupos de rotas que cruzam a latitude especificada."""
    df = pd.read_excel(arquivo_origem)

    grupos = df.groupby(["PREFIXO", "DESCRICAO DA LINHA"])

    selecionados = [
        grupo
        for _, grupo in grupos
        if grupo["LAT"].max() > limite and grupo["LAT"].min() < limite
    ]

    if selecionados:
        return pd.concat(selecionados, ignore_index=True)
    return pd.DataFrame(columns=df.columns)

df_selecionado = selecionar_rotas_que_cruzam()
df_selecionado.to_excel(ARQUIVO_DESTINO, index=False)