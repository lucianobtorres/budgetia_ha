from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest

from config import ColunasTransacoes
from finance.domain.models.transaction import Transaction
from finance.infrastructure.persistence.data_context import FinancialDataContext
from finance.infrastructure.persistence.excel_transaction_repository import (
    ExcelTransactionRepository,
)


@pytest.fixture
def mock_context():
    context = MagicMock(spec=FinancialDataContext)
    # DataFrame inicial vazio com as colunas corretas do layout
    df_empty = pd.DataFrame(
        columns=[
            ColunasTransacoes.ID,
            ColunasTransacoes.DATA,
            ColunasTransacoes.TIPO,
            ColunasTransacoes.CATEGORIA,
            ColunasTransacoes.DESCRICAO,
            ColunasTransacoes.VALOR,
            ColunasTransacoes.STATUS,
        ]
    )
    context.get_dataframe.return_value = df_empty
    return context


def test_save_new_transaction_generates_id(mock_context):
    """Testa se uma nova transação recebe um ID incremental."""
    repo = ExcelTransactionRepository(mock_context)
    tx = Transaction(
        data=date(2024, 1, 1),
        tipo="Despesa",
        categoria="Alimentação",
        descricao="Pizza",
        valor=80.0,
    )

    saved_tx = repo.save(tx)
    assert saved_tx.id == 1

    # Verifica se o context recebeu o DataFrame atualizado
    args, _ = mock_context.update_dataframe.call_args
    updated_df = args[1]
    assert len(updated_df) == 1
    assert updated_df.iloc[0][ColunasTransacoes.ID] == 1


def test_get_by_id_returns_entity(mock_context):
    """Testa se a busca por ID converte corretamente a linha para Entidade."""
    df_with_data = pd.DataFrame(
        [
            {
                ColunasTransacoes.ID: 99,
                ColunasTransacoes.DATA: pd.to_datetime("2024-02-15"),
                ColunasTransacoes.TIPO: "Receita",
                ColunasTransacoes.CATEGORIA: "Salário",
                ColunasTransacoes.DESCRICAO: "Job",
                ColunasTransacoes.VALOR: 5000.0,
                ColunasTransacoes.STATUS: "Concluído",
            }
        ]
    )
    mock_context.get_dataframe.return_value = df_with_data

    repo = ExcelTransactionRepository(mock_context)
    tx = repo.get_by_id(99)

    assert tx is not None
    assert tx.id == 99
    assert tx.tipo == "Receita"
    assert tx.valor == 5000.0
    assert isinstance(tx.data, date)


def test_delete_transaction(mock_context):
    """Testa a remoção de uma transação."""
    df_with_data = pd.DataFrame(
        [{ColunasTransacoes.ID: 10}, {ColunasTransacoes.ID: 20}]
    )
    mock_context.get_dataframe.return_value = df_with_data

    repo = ExcelTransactionRepository(mock_context)
    success = repo.delete(10)

    assert success is True
    args, _ = mock_context.update_dataframe.call_args
    updated_df = args[1]
    assert len(updated_df) == 1
    assert 10 not in updated_df[ColunasTransacoes.ID].values
