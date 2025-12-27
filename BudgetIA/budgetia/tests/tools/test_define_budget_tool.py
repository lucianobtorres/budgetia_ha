# Em: tests/tools/test_define_budget_tool.py
from unittest.mock import MagicMock  # Importar ANY

from finance.planilha_manager import PlanilhaManager  # Ainda precisamos do tipo
from finance.tools.define_budget_tool import DefineBudgetTool


def test_define_budget_tool_cria_novo_orcamento(
    plan_manager_para_ferramentas: PlanilhaManager,  # Não usamos, mas a fixture existe
) -> None:
    """
    Testa se a ferramenta consegue criar um novo orçamento
    chamando as funções injetadas.
    """
    # ARRANGE
    categoria = "Alimentação"
    valor_limite = 700.0
    periodo = "Mensal"
    observacoes = "Mercado e restaurantes"

    # Criamos mocks para as funções
    mock_add_budget = MagicMock(
        return_value=f"Novo orçamento para '{categoria}' criado."
    )
    mock_save = MagicMock()

    # ACT
    # --- CORREÇÃO: Injeta os mocks no __init__ ---
    tool = DefineBudgetTool(add_budget_func=mock_add_budget, save_func=mock_save)
    # --- FIM DA CORREÇÃO ---

    resultado_string = tool.run(
        categoria=categoria,
        valor_limite=valor_limite,
        periodo=periodo,
        observacoes=observacoes,
    )

    # ASSERT
    # 1. Verifica a mensagem de retorno
    assert f"Novo orçamento para '{categoria}' criado." in resultado_string

    # 2. Verifica se as funções foram chamadas
    mock_add_budget.assert_called_once_with(
        categoria=categoria,
        valor_limite=valor_limite,
        periodo=periodo,
        observacoes=observacoes,
    )
    mock_save.assert_called_once()


def test_define_budget_tool_atualiza_orcamento_existente(
    plan_manager_para_ferramentas: PlanilhaManager,  # Não usamos, mas a fixture existe
) -> None:
    """
    Testa se a ferramenta consegue atualizar um orçamento existente
    chamando as funções injetadas.
    """
    # ARRANGE
    categoria = "Transporte"
    novo_valor_limite = 250.0
    novas_observacoes = "Aumento gasolina"

    # Criamos mocks para as funções
    mock_add_budget = MagicMock(
        return_value=f"Orçamento para '{categoria}' atualizado."
    )
    mock_save = MagicMock()

    # ACT
    # --- CORREÇÃO: Injeta os mocks no __init__ ---
    tool = DefineBudgetTool(add_budget_func=mock_add_budget, save_func=mock_save)
    # --- FIM DA CORREÇÃO ---

    resultado_string = tool.run(
        categoria=categoria,
        valor_limite=novo_valor_limite,
        periodo="Mensal",
        observacoes=novas_observacoes,
    )

    # ASSERT
    # 1. Verifica a mensagem de retorno
    assert f"Orçamento para '{categoria}' atualizado." in resultado_string

    # 2. Verifica se as funções foram chamadas
    mock_add_budget.assert_called_once_with(
        categoria=categoria,
        valor_limite=novo_valor_limite,
        periodo="Mensal",
        observacoes=novas_observacoes,
    )
    mock_save.assert_called_once()
