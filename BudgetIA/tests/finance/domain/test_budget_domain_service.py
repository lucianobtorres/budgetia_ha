from datetime import date
from unittest.mock import MagicMock

import pytest

from finance.domain.models.budget import Budget
from finance.domain.models.transaction import Transaction
from finance.domain.services.budget_service import BudgetDomainService


@pytest.fixture
def mock_repos():
    return MagicMock(), MagicMock()


def test_recalculate_budgets_sums_correctly(mock_repos):
    """Testa se o serviço soma corretamente as transações por categoria."""
    mock_budget_repo, mock_tx_repo = mock_repos

    # Orçamento: Alimentação (Limite 1000)
    mock_budget_repo.list_all.return_value = [
        Budget(categoria="Alimentação", limite=1000.0, gasto_atual=0.0)
    ]

    # Transações: 2 de Alimentação (150 + 50) e 1 de Lazer (100)
    mock_tx_repo.list_all.return_value = [
        Transaction(
            data=date(2024, 1, 1),
            tipo="Despesa",
            categoria="Alimentação",
            descricao="A",
            valor=150.0,
        ),
        Transaction(
            data=date(2024, 1, 1),
            tipo="Despesa",
            categoria="Alimentação",
            descricao="B",
            valor=50.0,
        ),
        Transaction(
            data=date(2024, 1, 1),
            tipo="Despesa",
            categoria="Lazer",
            descricao="C",
            valor=100.0,
        ),
    ]

    service = BudgetDomainService(mock_budget_repo, mock_tx_repo)
    service.recalculate_budgets(month=1, year=2024)

    # Verifica se o save foi chamado com gasto_atual = 200.0 (150 + 50)
    saved_budget = mock_budget_repo.save.call_args[0][0]
    assert saved_budget.categoria == "Alimentação"
    assert saved_budget.gasto_atual == 200.0
    assert saved_budget.percentual_gasto == 20.0


def test_recalculate_budgets_handles_no_transactions(mock_repos):
    """Testa se zera o gasto se não houver transações."""
    mock_budget_repo, mock_tx_repo = mock_repos

    mock_budget_repo.list_all.return_value = [
        Budget(categoria="Alimentação", limite=1000.0, gasto_atual=500.0)
    ]
    mock_tx_repo.list_all.return_value = []  # Nenhuma transação

    service = BudgetDomainService(mock_budget_repo, mock_tx_repo)
    service.recalculate_budgets(month=1, year=2024)

    saved_budget = mock_budget_repo.save.call_args[0][0]
    assert saved_budget.gasto_atual == 0.0


def test_add_or_update_budget_logic(mock_repos):
    """Testa a regra de não duplicar categorias."""
    mock_budget_repo, _ = mock_repos

    # Simula que já existe Alimentação
    existing = Budget(id=1, categoria="Alimentação", limite=500.0)
    mock_budget_repo.get_by_category.return_value = existing

    service = BudgetDomainService(mock_budget_repo, MagicMock())
    service.add_or_update_budget("Alimentação", 800.0)

    # Deve atualizar o existente em vez de criar novo
    saved_budget = mock_budget_repo.save.call_args[0][0]
    assert saved_budget.id == 1
    assert saved_budget.limite == 800.0
