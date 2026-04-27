# src/application/notifications/rules/economy/__tests__/test_semantic_anomaly_rule.py
from unittest.mock import patch

import pandas as pd
import pytest

import config
from application.notifications.rules.economy.semantic_anomaly_rule import (
    SemanticAnomalyRule,
)


@pytest.fixture
def mock_embedding_service():
    with patch(
        "application.notifications.rules.economy.semantic_anomaly_rule.EmbeddingService"
    ) as mock:
        service = mock.return_value

        # Mock de similaridade: 1.0 para iguais, 0.1 para diferentes
        def side_effect(v1, v2):
            if v1 == "vec_food" and v2 == "vec_food":
                return 1.0
            return 0.1

        service.cosine_similarity.side_effect = side_effect

        def get_emb(text):
            if "Alimentação" in text or "Pizza" in text:
                return "vec_food"
            return "vec_other"

        service.get_embedding.side_effect = get_emb
        yield service


def test_semantic_anomaly_rule_triggers_on_mismatch(mock_embedding_service):
    # Setup
    rule = SemanticAnomalyRule(threshold_similarity=0.5, lookback_n=5)

    # Transação anômala: "Compra de Pneus" em "Alimentação"
    df = pd.DataFrame(
        [
            {
                config.ColunasTransacoes.TIPO: config.ValoresTipo.DESPESA,
                config.ColunasTransacoes.DESCRICAO: "Compra de Pneus",
                config.ColunasTransacoes.CATEGORIA: "Alimentação",
                config.ColunasTransacoes.VALOR: 500.0,
            }
        ]
    )

    result = rule.should_notify(df, pd.DataFrame(), {})

    assert result.triggered is True
    assert "Compra de Pneus" in result.message_template
    assert "Alimentação" in result.message_template


def test_semantic_anomaly_rule_does_not_trigger_on_match(mock_embedding_service):
    # Setup
    rule = SemanticAnomalyRule(threshold_similarity=0.5, lookback_n=5)

    # Transação coerente: "Pizza" em "Alimentação"
    df = pd.DataFrame(
        [
            {
                config.ColunasTransacoes.TIPO: config.ValoresTipo.DESPESA,
                config.ColunasTransacoes.DESCRICAO: "Pizza de Pepperoni",
                config.ColunasTransacoes.CATEGORIA: "Alimentação",
                config.ColunasTransacoes.VALOR: 80.0,
            }
        ]
    )

    result = rule.should_notify(df, pd.DataFrame(), {})

    assert result.triggered is False
