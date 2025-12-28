# Em: tests/services/test_insight_service.py

from unittest.mock import MagicMock

import pandas as pd
import pytest

import config
from config import ColunasOrcamentos, ColunasTransacoes
from finance.repositories.budget_repository import BudgetRepository
from finance.repositories.insight_repository import InsightRepository
from finance.repositories.transaction_repository import TransactionRepository
from finance.services.insight_service import InsightService


@pytest.fixture
def insight_service() -> InsightService:
    """Retorna uma instância limpa do InsightService para cada teste."""
    mock_transaction_repo = MagicMock(spec=TransactionRepository)
    mock_budget_repo = MagicMock(spec=BudgetRepository)
    mock_insight_repo = MagicMock(spec=InsightRepository)

    # Criar a instância do serviço com os mocks
    service = InsightService(
        transaction_repo=mock_transaction_repo,
        budget_repo=mock_budget_repo,
        insight_repo=mock_insight_repo,
    )
    return service


def test_gerar_analise_proativa_com_alertas(
    insight_service: InsightService,
) -> None:
    """
    Testa a geração de múltiplos insights:
    - Saldo Negativo
    - Orçamento Estourado
    - Orçamento em Alerta (novo)
    """
    # ARRANGE
    dados_orcamentos = {
        ColunasTransacoes.CATEGORIA: ["Alimentação", "Lazer", "Transporte"],
        ColunasOrcamentos.LIMITE: [1000.0, 500.0, 300.0],
        ColunasOrcamentos.GASTO: [1100.0, 475.0, 100.0],
        ColunasOrcamentos.PERCENTUAL: [110.0, 95.0, 33.3],
        # --- Status como o 'calcular_status_orcamentos' gera ---
        ColunasOrcamentos.STATUS: ["Estourado", "Alerta", "OK"],
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamentos,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS],
    ).fillna(0)

    saldo_total = -500.0

    # ACT
    insights = insight_service.gerar_analise_proativa(df_orcamentos, saldo_total)

    # ASSERT
    # (Deve encontrar 3 insights: Estourado, Alerta, Saldo Negativo)
    assert len(insights) == 3
    tipos_insights = {insight["tipo_insight"] for insight in insights}
    assert "Alerta de Orçamento" in tipos_insights
    assert "Aviso de Orçamento" in tipos_insights
    assert "Alerta de Saldo" in tipos_insights


def test_gerar_analise_proativa_cenario_saudavel(
    insight_service: InsightService,
) -> None:
    """
    Testa a geração de insight de "Sugestão de Economia" quando
    o saldo está positivo e os orçamentos estão "OK".
    """
    # ARRANGE
    dados_orcamentos = {
        ColunasTransacoes.CATEGORIA: ["Alimentação", "Lazer"],
        ColunasOrcamentos.LIMITE: [1000.0, 500.0],
        ColunasOrcamentos.GASTO: [700.0, 200.0],
        ColunasOrcamentos.PERCENTUAL: [70.0, 40.0],
        ColunasOrcamentos.STATUS: ["OK", "OK"],  # Status correto
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamentos,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS],
    ).fillna(0)

    saldo_total = 2500.0

    # ACT
    insights = insight_service.gerar_analise_proativa(df_orcamentos, saldo_total)

    # ASSERT
    # (Deve encontrar 1 insight: Sugestão de Economia)
    assert len(insights) == 1
    assert insights[0]["tipo_insight"] == "Sugestão de Economia"
