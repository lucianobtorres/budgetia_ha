# src/application/notifications/rules/economy/anomaly_detection_rule.py
from typing import Any

import pandas as pd

import config
from application.notifications.models.notification_message import NotificationPriority
from application.notifications.models.rule_result import RuleResult
from application.notifications.rules.base_rule import IFinancialRule
from core.logger import get_logger

logger = get_logger("AnomalyDetectionRule")


class AnomalyDetectionRule(IFinancialRule):  # type: ignore[misc]
    """
    Regra: Detecta transações recentes que são significativamente maiores que a média histórica da categoria.
    """

    def __init__(self, std_dev_threshold: float = 3.0, lookback_days: int = 2):
        self.std_dev_threshold = std_dev_threshold
        self.lookback_days = lookback_days

    @property
    def rule_name(self) -> str:
        return "anomaly_detection"

    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame,
        user_profile: dict[str, Any],
    ) -> RuleResult:
        if transactions_df.empty:
            return RuleResult(triggered=False)

        # 1. Identificar transações recentes (últimos N dias)
        transactions_df[config.ColunasTransacoes.DATA] = pd.to_datetime(
            transactions_df[config.ColunasTransacoes.DATA]
        )
        now = pd.Timestamp.now()
        recent_txs = transactions_df[
            transactions_df[config.ColunasTransacoes.DATA]
            >= (now - pd.Timedelta(days=self.lookback_days))
        ]

        if recent_txs.empty:
            return RuleResult(triggered=False)

        # 2. Calcular estatísticas históricas por categoria
        # Usamos todo o histórico para calcular a média e desvio padrão
        stats = (
            transactions_df.groupby(config.ColunasTransacoes.CATEGORIA)[
                config.ColunasTransacoes.VALOR
            ]
            .agg(["mean", "std"])
            .fillna(0)
        )

        anomalies = []
        for _, tx in recent_txs.iterrows():
            cat = tx[config.ColunasTransacoes.CATEGORIA]
            val = float(tx[config.ColunasTransacoes.VALOR])

            if cat not in stats.index:
                continue

            mean = stats.loc[cat, "mean"]
            std = stats.loc[cat, "std"]

            # Se o desvio padrão for 0 (poucas transações), pulamos
            if std == 0:
                continue

            # Se o valor atual for maior que (Média + X * Desvio Padrão)
            if val > (mean + self.std_dev_threshold * std):
                msg = (
                    f"🔍 Detectei um gasto incomum em *{cat}*: R$ {val:.2f} "
                    f"(a média habitual é R$ {mean:.2f})."
                )
                anomalies.append(msg)

        if anomalies:
            full_msg = "🤔 **Gasto Incomum Detectado**\n\n" + "\n".join(anomalies)
            return RuleResult(
                triggered=True,
                message_template=full_msg,
                priority=NotificationPriority.MEDIUM,
                category="anomaly",
            )

        return RuleResult(triggered=False)
