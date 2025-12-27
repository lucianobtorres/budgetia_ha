import os
import sys

# Adiciona src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from finance.factory import FinancialSystemFactory
from core.user_config_service import UserConfigService
from finance.storage.excel_storage_handler import ExcelStorageHandler

# Alvo: Usuário real para ver os dados dele
USERNAME = "lucianobtorres" 

def debug_budgets():
    print(f"--- Debugging Budgets para '{USERNAME}' ---")
    config_service = UserConfigService(USERNAME)
    path = config_service.get_planilha_path()
    
    if not path:
        print("Erro: Planilha não encontrada para o usuário.")
        return

    storage = ExcelStorageHandler(path)
    
    # Cria o manager (vai carregar dados)
    # IMPORTANTE: Isso vai ler do Cache se estiver lá. 
    # Mas o recalculate vai ler as transações do Repo.
    manager = FinancialSystemFactory.create_manager(storage, config_service)
    
    print("\n--- Forçando Recálculo ---")
    # Isso chama o BudgetService com os prints que adicionei
    manager.recalculate_budgets()
    
    print("\n--- Verificando Resultado em Memória ---")
    df_orc = manager.visualizar_dados("Orçamentos")
    print(df_orc[['Categoria', 'Gasto', 'Limite', 'Status']])

if __name__ == "__main__":
    debug_budgets()
