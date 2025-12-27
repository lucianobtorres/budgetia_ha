import os
import sys

import pandas as pd

# Tenta encontrar a pasta 'data' usando o 'config.py'
try:
    # Adiciona 'src' ao path para encontrar o 'config'
    src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    import config

    DATA_DIR = config.DATA_DIR
    print(f"Usando pasta de dados do config: {DATA_DIR}")
except ImportError:
    print("AVISO: Módulo 'config' não encontrado. Salvando em 'data/'.")
    DATA_DIR = "data"
    os.makedirs(DATA_DIR, exist_ok=True)


# 1. Define o schema customizado e os dados de exemplo
#    (Note os nomes das colunas e os valores negativos)
data = {
    "Data da Operação": [
        "2025-11-01",
        "2025-11-03",
        "2025-11-05",
        "2025-11-06",
        "2025-11-07",
    ],
    "Detalhes": ["Salário Mensal", "Aluguel", "Supermercado iFood", "Uber", "Cinema"],
    "Valor (R$)": [5000.00, -1500.00, -450.75, -30.50, -80.00],
    "Minha Categoria": ["Receita", "Moradia", "Alimentação", "Transporte", "Lazer"],
}

# 2. Cria o DataFrame
df_exemplo = pd.DataFrame(data)

# 3. Define o nome e o caminho do arquivo
file_name = "planilha_exemplo_diferente.xlsx"
file_path = os.path.join(DATA_DIR, file_name)

# 4. Salva o arquivo Excel
try:
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df_exemplo.to_excel(writer, sheet_name="Meu Extrato", index=False)

        # Adiciona uma segunda aba inútil
        df_dummy = pd.DataFrame({"ID": [101, 102]})
        df_dummy.to_excel(writer, sheet_name="OutraAba", index=False)

    print(f"SUCESSO: Arquivo de teste criado em: {file_path}")
    print("Este arquivo tem a aba 'Meu Extrato' e usa valores negativos para despesas.")
except Exception as e:
    print(f"ERRO ao criar arquivo de exemplo: {e}")
