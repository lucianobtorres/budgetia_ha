import sys
import os
import pandas as pd
import datetime

# Adiciona src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from finance.services.budget_service import BudgetService
from config import ColunasTransacoes, ColunasOrcamentos, ValoresTipo

def debug_service():
    service = BudgetService()
    
    # 1. Mock Transactions (Matching user Screenshot)
    # Date: 25 DEZ (assuming 2025 based on screenshot header)
    # Category: "Lazer" (Cyan pill)
    # Value: 20.00
    # Type: "Despesa" (implied by red color, but let's test)
    
    data_transacoes = {
        ColunasTransacoes.ID: [1, 2, 3],
        ColunasTransacoes.DATA: [
            datetime.datetime(2025, 12, 25), 
            datetime.datetime(2025, 12, 25),
            datetime.datetime(2025, 12, 24)
        ],
        ColunasTransacoes.TIPO: [ValoresTipo.DESPESA, ValoresTipo.DESPESA, ValoresTipo.DESPESA],
        ColunasTransacoes.CATEGORIA: ["Alimentação", "Jogos de azar", "Uber"], # Note: Transaction category is "Jogos de azar" but the Pill/Budget is "Lazer"? No wait.
        # Screenshot 2: "Jogos de azar" is the DESCRIPTION (White text). "Lazer" is the CATEGORY (Cyan Pill).
        # So ColunasTransacoes.CATEGORIA should be "Lazer".
        # Let's verify if user put "Jogos de azar" as description and "Lazer" as category.
        ColunasTransacoes.DESCRICAO: ["Supermercado", "Jogos de azar", "Uber"],
        ColunasTransacoes.VALOR: [851.00, 20.00, 11.00]
    }
    
    # CORRECTING DATA:
    # Transaction 1: Desc: Supermercado, Cat: Alimentação
    # Transaction 2: Desc: Jogos de azar, Cat: Lazer
    # Transaction 3: Desc: Uber, Cat: Transporte
    
    df_transacoes = pd.DataFrame({
        ColunasTransacoes.ID: [1, 2, 3],
        ColunasTransacoes.DATA: [
            "2025-12-25", 
            "2025-12-25",
            "2025-12-24"
        ],
        ColunasTransacoes.TIPO: ["Despesa", "Despesa", "Despesa"],
        ColunasTransacoes.CATEGORIA: ["Alimentação", "Lazer", "Transporte"],
        ColunasTransacoes.DESCRICAO: ["Supermercado", "Jogos de azar", "Uber"],
        ColunasTransacoes.VALOR: [851.00, 20.00, 11.00]
    })
    
    # 2. Mock Budgets
    df_orcamentos = pd.DataFrame([
        {
            ColunasOrcamentos.ID: 1,
            ColunasOrcamentos.CATEGORIA: "Alimentação",
            ColunasOrcamentos.LIMITE: 1500.00, 
            ColunasOrcamentos.PERIODO: "Mensal"
        },
        {
            ColunasOrcamentos.ID: 2,
            ColunasOrcamentos.CATEGORIA: "Lazer",
            ColunasOrcamentos.LIMITE: 0.00, # Zero limit case
            ColunasOrcamentos.PERIODO: "Mensal"
        },
         {
            ColunasOrcamentos.ID: 3,
            ColunasOrcamentos.CATEGORIA: "Transporte",
            ColunasOrcamentos.LIMITE: 300.00, 
            ColunasOrcamentos.PERIODO: "Mensal"
        }
    ])
    
    print("\n--- Running Calculation ---")
    
    # Mock datetime.now() to be 2025-12-26? 
    # The actual code uses datetime.now(). If I run this today (2025), it should match.
    # WAIT! The current machine time is 2025-12-26 (Metadata says so).
    # So filtering for Year 2025, Month 12 is correct.
    
    result = service.calcular_status_orcamentos(df_transacoes, df_orcamentos)
    
    print("\n--- RESULTADO OBTIDO ---")
    print(result[[ColunasOrcamentos.CATEGORIA, ColunasOrcamentos.GASTO, ColunasOrcamentos.LIMITE, ColunasOrcamentos.STATUS]])

if __name__ == "__main__":
    debug_service()
