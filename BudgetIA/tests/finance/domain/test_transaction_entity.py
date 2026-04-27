from datetime import date

import pytest

from finance.domain.models.transaction import Transaction


def test_transaction_creation_valid():
    """Testa a criação de uma transação válida."""
    tx = Transaction(
        data=date(2024, 1, 1),
        tipo="Despesa",
        categoria="Alimentação",
        descricao="Almoço",
        valor=50.0,
    )
    assert tx.valor == 50.0
    assert tx.tipo == "Despesa"


def test_transaction_eh_despesa_helper():
    """Testa o helper que identifica se é despesa."""
    tx = Transaction(
        data=date.today(),
        tipo="Despesa",
        categoria="Alimentação",
        descricao="Almoço",
        valor=50.0,
    )
    assert tx.eh_despesa is True

    tx2 = Transaction(
        data=date.today(),
        tipo="Receita",
        categoria="Salário",
        descricao="Pagamento",
        valor=5000.0,
    )
    assert tx2.eh_despesa is False


def test_transaction_invalid_valor():
    """Testa se a entidade rejeita valores negativos."""
    with pytest.raises(ValueError, match="Valor deve ser positivo"):
        Transaction(
            data=date(2024, 1, 1),
            tipo="Despesa",
            categoria="Alimentação",
            descricao="Erro",
            valor=-10.0,
        )


def test_transaction_normalization():
    """Testa se a descrição é limpa automaticamente."""
    tx = Transaction(
        data=date(2024, 1, 1),
        tipo="Despesa",
        categoria="Alimentação",
        descricao="  Mercado Extra   ",
        valor=100.0,
    )
    assert tx.descricao == "Mercado Extra"
