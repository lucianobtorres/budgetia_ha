# Em: tests/tools/test_add_transaction_tool.py
from unittest.mock import MagicMock  # Importar ANY

from finance.planilha_manager import PlanilhaManager  # Ainda precisamos do tipo
from finance.tools.add_transaction_tool import AddTransactionTool


def test_add_transaction_tool_com_data(
    plan_manager_para_ferramentas: PlanilhaManager,  # Usamos a fixture para obter o 'context'
) -> None:
    """
    Testa se a ferramenta 'AdicionarTransacaoTool' chama as funções
    corretas e retorna a string esperada.
    """
    # ARRANGE
    # Criamos mocks para as funções que a Tool espera
    mock_add_transaction = MagicMock()
    mock_save = MagicMock()
    # Faz o mock de get_summary retornar um saldo para o teste
    mock_get_summary = MagicMock(return_value={"saldo": 1000.0})

    mock_recalculate_budgets = MagicMock()

    # Argumentos para a ferramenta
    data = "2025-10-17"
    tipo = "Despesa"
    categoria = "Alimentação"
    valor = 50.75
    descricao = "Almoço"
    saldo_esperado_str = "1.000,00"  # R$ 1.000,00 formatado

    # ACT
    # --- CORREÇÃO: Injeta os mocks no __init__ ---
    tool = AddTransactionTool(
        add_transaction_func=mock_add_transaction,
        save_func=mock_save,
        get_summary_func=mock_get_summary,
        recalculate_budgets_func=mock_recalculate_budgets,
    )
    # --- FIM DA CORREÇÃO ---

    resultado_string = tool.run(
        tipo=tipo,
        categoria=categoria,
        descricao=descricao,
        valor=valor,
        data=data,
    )

    # ASSERT
    # 1. Verifica a resposta para a IA
    assert "adicionada com sucesso" in resultado_string.lower()
    assert saldo_esperado_str in resultado_string

    # 2. Verifica se as funções corretas foram chamadas
    mock_add_transaction.assert_called_once_with(
        data=data,
        tipo=tipo,
        categoria=categoria,
        descricao=descricao,
        valor=valor,
        status="Concluído",  # Verifica o status padrão
        parcelas=1,
    )

    # 3. Verifica se o recálculo do orçamento foi chamado
    mock_recalculate_budgets.assert_called_once()

    mock_save.assert_called_once()
    mock_get_summary.assert_called_once()
