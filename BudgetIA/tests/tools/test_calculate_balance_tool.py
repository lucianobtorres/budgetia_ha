# Em: tests/tools/test_calculate_balance_tool.py

import pandas as pd

import config
from finance.planilha_manager import PlanilhaManager
from finance.tools.calculate_balance_tool import CalcularSaldoTotalTool


def test_calcular_saldo_total_tool_executa_corretamente(
    plan_manager_para_ferramentas: PlanilhaManager,
) -> None:
    """
    Testa se a ferramenta 'CalcularSaldoTotalTool' chama o plan_manager
    e retorna a string formatada corretamente.
    """
    # ARRANGE
    # Plantamos os dados de transação direto na memória do manager
    dados_transacoes = {
        "Tipo (Receita/Despesa)": ["Receita", "Despesa", "Receita"],
        "Valor": [5000.0, 1000.0, 200.0],
        "Categoria": ["Salário", "Aluguel", "Freelance"],
    }
    df_transacoes = pd.DataFrame(
        dados_transacoes,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES],
    ).fillna("")

    plan_manager_para_ferramentas.dfs[config.NomesAbas.TRANSACOES] = df_transacoes

    # (5000 + 200) - 1000 = 4200
    resultado_esperado = "R$ 4.200,00"

    # ACT
    # Instanciamos a ferramenta com o manager mockado
    tool = CalcularSaldoTotalTool(planilha_manager=plan_manager_para_ferramentas)
    resultado_string = tool.run()

    # ASSERT
    assert resultado_esperado in resultado_string
    assert "saldo financeiro total" in resultado_string.lower()
