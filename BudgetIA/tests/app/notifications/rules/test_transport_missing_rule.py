# tests/app/notifications/rules/test_transport_missing_rule.py
from datetime import datetime, timedelta

import pandas as pd
import pytest

from app.notifications.models.notification_message import NotificationPriority
from app.notifications.rules.transport_missing_rule import TransportMissingRule
from config import ColunasTransacoes


class TestTransportMissingRule:
    """Testes para a regra de transporte faltante."""

    def test_rule_name(self):
        """Testa se o nome da regra está correto."""
        rule = TransportMissingRule()
        assert rule.rule_name == "transport_missing"

    def test_no_transport_in_last_2_days_triggers(self):
        """Testa se a regra é acionada quando não há transporte nos últimos 2 dias."""
        rule = TransportMissingRule(days_threshold=2)

        # Cria DataFrame com transporte de 3 dias atrás
        three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        df = pd.DataFrame(
            {
                ColunasTransacoes.DATA: [three_days_ago],
                ColunasTransacoes.CATEGORIA: ["Transporte"],
                ColunasTransacoes.VALOR: [10.0],
            }
        )

        result = rule.should_notify(df, pd.DataFrame(), {})

        assert result.triggered is True
        assert result.priority == NotificationPriority.MEDIUM
        assert "Transporte" in result.message_template
        assert result.context["days"] == 2

    def test_recent_transport_does_not_trigger(self):
        """Testa se a regra NÃO é acionada quando existe transporte recente."""
        rule = TransportMissingRule(days_threshold=2)

        # Cria DataFrame com transporte de hoje
        today = datetime.now().strftime("%Y-%m-%d")
        df = pd.DataFrame(
            {
                ColunasTransacoes.DATA: [today],
                ColunasTransacoes.CATEGORIA: ["Transporte"],
                ColunasTransacoes.VALOR: [15.0],
            }
        )

        result = rule.should_notify(df, pd.DataFrame(), {})

        assert result.triggered is False

    def test_empty_dataframe_triggers(self):
        """Testa se DataFrame vazio ACIONA a regra (sem transações = sem transporte)."""
        rule = TransportMissingRule()

        result = rule.should_notify(pd.DataFrame(), pd.DataFrame(), {})

        # DataFrame vazio = nenhuma transação = nenhum transporte = DEVE notificar
        assert result.triggered is True
        assert "não tem nenhuma transação registrada" in result.message_template

    def test_custom_threshold(self):
        """Testa threshold customizado de dias."""
        rule = TransportMissingRule(days_threshold=5)

        # Transporte de 4 dias atrás (dentro do threshold de 5 dias)
        four_days_ago = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")
        df = pd.DataFrame(
            {
                ColunasTransacoes.DATA: [four_days_ago],
                ColunasTransacoes.CATEGORIA: ["Transporte"],
                ColunasTransacoes.VALOR: [20.0],
            }
        )

        result = rule.should_notify(df, pd.DataFrame(), {})

        # NÃO deve acionar porque 4 dias < 5 dias threshold
        assert result.triggered is False

        # Agora testa com 6 dias atrás (fora do threshold)
        six_days_ago = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
        df2 = pd.DataFrame(
            {
                ColunasTransacoes.DATA: [six_days_ago],
                ColunasTransacoes.CATEGORIA: ["Transporte"],
                ColunasTransacoes.VALOR: [20.0],
            }
        )

        result2 = rule.should_notify(df2, pd.DataFrame(), {})

        # DEVE acionar porque 6 dias > 5 dias threshold
        assert result2.triggered is True
        assert result2.context["days"] == 5

    def test_other_categories_ignored(self):
        """Testa se outras categorias além de Transporte são ignoradas."""
        rule = TransportMissingRule(days_threshold=2)

        # DataFrame com outras categorias recentes mas sem Transporte
        today = datetime.now().strftime("%Y-%m-%d")
        df = pd.DataFrame(
            {
                ColunasTransacoes.DATA: [today, today],
                ColunasTransacoes.CATEGORIA: ["Alimentação", "Saúde"],
                ColunasTransacoes.VALOR: [50.0, 100.0],
            }
        )

        result = rule.should_notify(df, pd.DataFrame(), {})

        # DEVE acionar porque não há transporte
        assert result.triggered is True

    def test_result_to_message(self):
        """Testa a conversão do RuleResult para NotificationMessage."""
        rule = TransportMissingRule(days_threshold=2)

        three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        df = pd.DataFrame(
            {
                ColunasTransacoes.DATA: [three_days_ago],
                ColunasTransacoes.CATEGORIA: ["Transporte"],
                ColunasTransacoes.VALOR: [10.0],
            }
        )

        result = rule.should_notify(df, pd.DataFrame(), {})
        message = result.to_message()

        assert "2 dias" in message.text
        assert message.priority == NotificationPriority.MEDIUM
        assert message.category == "financial_reminder"
