import pandas as pd

ARQUIVO_MALHA = "Malha_Formatada.csv"
CIDADE_ALVO = "FEIRA DE SANTANA"

# Lê o CSV com separador ponto e vírgula
df = pd.read_csv(ARQUIVO_MALHA, sep=';', encoding='utf-8-sig')

# Filtra registros da localidade desejada
feira = df[df['LOCALIDADE'].str.upper().str.contains(CIDADE_ALVO)].copy()

# Converte o horário para datetime
feira['HORARIO'] = pd.to_datetime(feira['HORARIO'], format='%H:%M', errors='coerce')

# Intervalos de quatro horas
time_bins = [0, 4, 8, 12, 16, 20, 24]
faixas = [
    '00:00-03:59',
    '04:00-07:59',
    '08:00-11:59',
    '12:00-15:59',
    '16:00-19:59',
    '20:00-23:59',
]

feira['Faixa'] = pd.cut(
    feira['HORARIO'].dt.hour,
    bins=time_bins,
    labels=faixas,
    right=False,
    include_lowest=True,
)

contagem = feira['Faixa'].value_counts().sort_index()
resultado = contagem.reset_index()
resultado.columns = ['Faixa de horário', 'Quantidade de incidências']

# Adiciona linha de totais
total = resultado['Quantidade de incidências'].sum()
total_row = pd.DataFrame(
    {
        'Faixa de horário': ['Total'],
        'Quantidade de incidências': [total]
    }
)
resultado = pd.concat([resultado, total_row], ignore_index=True)

print(resultado)
