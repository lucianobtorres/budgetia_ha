# Em: tests/services/test_transaction_service.py

import pandas as pd
import pytest

import config
from config import ColunasTransacoes, SummaryKeys, ValoresTipo
from finance.services.transaction_service import TransactionService


@pytest.fixture
def transaction_service() -> TransactionService:
    """Retorna uma instância limpa do TransactionService para cada teste."""
    return TransactionService()


def test_get_summary_calcula_corretamente(
    transaction_service: TransactionService,
) -> None:
    """
    Testa o cálculo de receitas, despesas e saldo.
    (Movido de test_financial_calculator.py)
    """
    # ARRANGE
    dados_transacoes = {
        ColunasTransacoes.TIPO: [
            ValoresTipo.RECEITA,
            ValoresTipo.DESPESA,
            ValoresTipo.RECEITA,
            ValoresTipo.DESPESA,
        ],
        ColunasTransacoes.VALOR: [5000.0, 150.0, 200.0, 80.50],
        ColunasTransacoes.CATEGORIA: ["Salário", "Lazer", "Freelance", "Alimentação"],
    }
    df_transacoes = pd.DataFrame(
        dados_transacoes, columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES]
    ).fillna("")

    receitas_esperadas = 5200.0
    despesas_esperadas = 230.50
    saldo_esperado = 4969.50

    # ACT
    resumo = transaction_service.get_summary(df_transacoes)

    # --- CORREÇÃO (KeyError - Falha 1) ---
    assert resumo[SummaryKeys.RECEITAS] == pytest.approx(receitas_esperadas)
    assert resumo[SummaryKeys.DESPESAS] == pytest.approx(despesas_esperadas)
    assert resumo[SummaryKeys.SALDO] == pytest.approx(saldo_esperado)
    # --- FIM DA CORREÇÃO ---


def test_get_summary_dataframe_vazio(
    transaction_service: TransactionService,
) -> None:
    """
    Testa se o resumo retorna zeros para um DataFrame vazio.
    """
    # ARRANGE
    df_vazio = pd.DataFrame(columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES])

    # ACT
    resumo = transaction_service.get_summary(df_vazio)

    # ASSERT
    assert resumo[SummaryKeys.RECEITAS] == 0.0
    assert resumo[SummaryKeys.DESPESAS] == 0.0
    assert resumo[SummaryKeys.SALDO] == 0.0


def test_get_expenses_by_category_ranking_correto(
    transaction_service: TransactionService,
) -> None:
    """
    Testa a soma de despesas por categoria e o ranking top_n.
    (Movido de test_financial_calculator.py)
    """
    # ARRANGE
    dados_transacoes = {
        "Tipo (Receita/Despesa)": [
            "Despesa",
            "Despesa",
            "Receita",  # Deve ser ignorada
            "Despesa",
            "Despesa",
        ],
        "Categoria": ["Alimentação", "Lazer", "Salário", "Alimentação", "Moradia"],
        "Valor": [100.0, 50.0, 5000.0, 150.0, 300.0],
    }
    df_transacoes = pd.DataFrame(
        dados_transacoes,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES],
    ).fillna("")

    # Moradia: 300.0
    # Alimentação: 250.0
    # Lazer: 50.0

    # ACT
    top_expenses = transaction_service.get_expenses_by_category(df_transacoes, top_n=2)

    # ASSERT
    assert isinstance(top_expenses, pd.Series)
    assert len(top_expenses) == 2
    assert top_expenses.index[0] == "Moradia"
    assert top_expenses.values[0] == pytest.approx(300.0)
    assert top_expenses.index[1] == "Alimentação"
    assert top_expenses.values[1] == pytest.approx(250.0)


def test_get_expenses_by_category_sem_despesas(
    transaction_service: TransactionService,
) -> None:
    """
    Testa o comportamento quando não há nenhuma transação de 'Despesa'.
    (Movido de test_financial_calculator.py)
    """
    # ARRANGE
    dados_transacoes = {
        ColunasTransacoes.TIPO: ["Receita", "Receita"],
        ColunasTransacoes.CATEGORIA: ["Salário", "Freelance"],
        ColunasTransacoes.VALOR: [5000.0, 300.0],
    }
    df_transacoes = pd.DataFrame(
        dados_transacoes,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES],
    ).fillna("")

    # ACT
    top_expenses = transaction_service.get_expenses_by_category(df_transacoes, top_n=3)

    # ASSERT
    assert isinstance(top_expenses, pd.Series)
    assert top_expenses.empty
