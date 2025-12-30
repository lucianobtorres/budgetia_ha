# src/app/notifications/rules/transport_missing_rule.py
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

import config
from core.logger import get_logger
from application.notifications.models.notification_message import NotificationPriority

logger = get_logger("TransportMissingRule")
from application.notifications.models.rule_result import RuleResult
from application.notifications.rules.base_rule import IFinancialRule


class TransportMissingRule(IFinancialRule): # type: ignore[misc]
    """
    Regra: Detecta se o usuário não registrou despesas de transporte
    nos últimos N dias (configurável).

    Esta é uma regra de negócio pura - sem dependência de canais,
    configuração de usuário, ou infraestrutura.
    """

    def __init__(self, days_threshold: int = 2):
        """
        Inicializa a regra com threshold de dias.

        Args:
            days_threshold: Número de dias sem transporte para disparar alerta.
        """
        self.days_threshold = days_threshold

    @property
    def rule_name(self) -> str:
        return "transport_missing"

    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame,
        user_profile: dict[str, Any],
    ) -> RuleResult:
        """
        Verifica se falta registro de transporte nos últimos N dias.

        Args:
            transactions_df: DataFrame com transações.
            budgets_df: Não usado por esta regra.
            user_profile: Não usado por esta regra.

        Returns:
            RuleResult com triggered=True se deve notificar.
        """
        logger.debug(
            f"Verificando transporte dos últimos {self.days_threshold} dias..."
        )

        # Validação: DataFrame vazio significa SEM transações = SEM transporte = DEVE NOTIFICAR
        if transactions_df.empty:
            logger.info("DataFrame vazio. Nenhuma transação registrada. TRIGGERED!")
            return RuleResult(
                triggered=True,
                message_template=(
                    "Olá! Notei que você não tem nenhuma transação registrada ainda, "
                    "incluindo gastos com 'Transporte'. "
                    "Gostaria de começar a registrar suas despesas agora?\n\n"
                    "(Eu sou seu assistente proativo. Esta é uma mensagem automática.)"
                ),
                context={"days": self.days_threshold},
                priority=NotificationPriority.MEDIUM,
                category="financial_reminder",
            )

        # Lógica extraída de proactive_jobs.py (linhas 76-84)
        df_copy = transactions_df.copy()
        df_copy[config.ColunasTransacoes.DATA] = pd.to_datetime(
            df_copy[config.ColunasTransacoes.DATA]
        )

        threshold_date = datetime.now() - timedelta(days=self.days_threshold)

        transport_recent = df_copy[
            (df_copy[config.ColunasTransacoes.CATEGORIA] == "Transporte")
            & (df_copy[config.ColunasTransacoes.DATA] >= threshold_date)
        ]

        if transport_recent.empty:
            logger.info(
                f"Nenhum transporte nos últimos {self.days_threshold} dias. TRIGGERED!"
            )
            return RuleResult(
                triggered=True,
                message_template=(
                    "Olá! Notei que você não registra gastos com 'Transporte' há {days} dias. "
                    "Gostaria de adicionar um gasto agora?\n\n"
                    "(Eu sou seu assistente proativo. Esta é uma mensagem automática.)"
                ),
                context={"days": self.days_threshold},
                priority=NotificationPriority.MEDIUM,
                category="financial_reminder",
            )
        else:
            logger.debug("Transporte encontrado. Não notificar.")
            return RuleResult(
                triggered=False,
                message_template="",
                context={},
                priority=NotificationPriority.LOW,
            )
