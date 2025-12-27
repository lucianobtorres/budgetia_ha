# Em: tests/tools/test_calculate_balance_tool.py
from unittest.mock import MagicMock  # Importar MagicMock

from finance.planilha_manager import PlanilhaManager  # Ainda precisamos do tipo
from finance.tools.calculate_balance_tool import CalcularSaldoTotalTool


def test_calcular_saldo_total_tool_executa_corretamente(
    plan_manager_para_ferramentas: PlanilhaManager,  # Não usamos, mas a fixture existe
) -> None:
    """
    Testa se a ferramenta 'CalcularSaldoTotalTool' chama a função injetada
    e retorna a string formatada corretamente.
    """
    # ARRANGE
    # Simulamos o retorno que o get_summary_func deve dar
    saldo_simulado = 4200.0
    resultado_esperado = "R$ 4.200,00"

    # Criamos o mock da função
    mock_get_summary = MagicMock(return_value={"saldo": saldo_simulado})

    # ACT
    # --- CORREÇÃO: Injeta o mock no __init__ ---
    tool = CalcularSaldoTotalTool(get_summary_func=mock_get_summary)
    # --- FIM DA CORREÇÃO ---

    resultado_string = tool.run()

    # ASSERT
    assert resultado_esperado in resultado_string
    mock_get_summary.assert_called_once()
