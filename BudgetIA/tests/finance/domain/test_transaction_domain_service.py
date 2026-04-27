from datetime import date
from unittest.mock import MagicMock

import pytest

from finance.domain.models.transaction import Transaction
from finance.domain.repositories.transaction_repository import ITransactionRepository
from finance.domain.services.transaction_service import TransactionDomainService


@pytest.fixture
def mock_repo():
    return MagicMock(spec=ITransactionRepository)


def test_add_transaction_single(mock_repo):
    """Testa criação de transação única sem parcelas."""
    service = TransactionDomainService(mock_repo)
    data = {
        "data": date(2024, 1, 1),
        "tipo": "Despesa",
        "categoria": "Lazer",
        "descricao": "Cinema",
        "valor": 40.0,
    }

    service.add_transaction(data)
    mock_repo.save.assert_called_once()
    saved_tx = mock_repo.save.call_args[0][0]
    assert saved_tx.descricao == "Cinema"


def test_add_transaction_with_installments(mock_repo):
    """Testa a geração correta de parcelas mensais."""
    service = TransactionDomainService(mock_repo)
    data = {
        "data": date(2024, 1, 10),
        "tipo": "Despesa",
        "categoria": "Eletrônicos",
        "descricao": "Celular",
        "valor": 500.0,
        "parcelas": 3,
    }

    results = service.add_transaction(data)
    assert len(results) == 3
    assert results[0].descricao == "Celular (1/3)"
    assert results[1].descricao == "Celular (2/3)"
    assert results[1].data == date(2024, 2, 10)
    assert results[2].data == date(2024, 3, 10)

    mock_repo.save_batch.assert_called_once_with(results)


def test_get_summary_calculation(mock_repo):
    """Testa o cálculo de resumo baseado em entidades."""
    mock_repo.list_all.return_value = [
        Transaction(
            data=date(2024, 1, 1),
            tipo="Receita",
            categoria="S",
            descricao="D",
            valor=1000.0,
        ),
        Transaction(
            data=date(2024, 1, 1),
            tipo="Despesa",
            categoria="S",
            descricao="D",
            valor=200.0,
        ),
        Transaction(
            data=date(2024, 1, 1),
            tipo="Despesa",
            categoria="S",
            descricao="D",
            valor=300.0,
        ),
    ]

    service = TransactionDomainService(mock_repo)
    summary = service.get_summary()

    assert summary["total_receitas"] == 1000.0
    assert summary["total_despesas"] == 500.0
    assert summary["saldo"] == 500.0
