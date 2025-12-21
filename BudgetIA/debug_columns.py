import pandas as pd
import os
from src.config import NomesAbas

# Path from the user logs
file_path = r"C:\Users\lucia\Documents\Projetos\Python\BudgetIA\BudgetIA\data\planilha_mestra copy - Copia (2).xlsx"

try:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        # Try default path just in case
        file_path = r"C:\Users\lucia\Documents\Projetos\Python\BudgetIA\BudgetIA\data\planilha_mestra.xlsx"
        print(f"Trying default: {file_path}")

    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Loading: {file_path}\n")
        df = pd.read_excel(file_path, sheet_name=NomesAbas.ORCAMENTOS)
        f.write("\n--- Columns in 'Meus Orçamentos' ---\n")
        for col in df.columns:
            f.write(f"'{col}'\n")
        
        f.write("\n--- First Row Data ---\n")
        if not df.empty:
            f.write(str(df.iloc[0].to_dict()))
        else:
            f.write("Dataframe is empty")
    print("Done.")

except Exception as e:
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {e}")
    print(f"Error: {e}")
