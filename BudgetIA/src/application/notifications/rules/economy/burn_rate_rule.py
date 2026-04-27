# src/application/notifications/rules/economy/burn_rate_rule.py
from datetime import datetime
from typing import Any

import pandas as pd

import config
from application.notifications.models.notification_message import NotificationPriority
from application.notifications.models.rule_result import RuleResult
from application.notifications.rules.base_rule import IFinancialRule
from core.logger import get_logger

logger = get_logger("BurnRateRule")


class BurnRateRule(IFinancialRule):  # type: ignore[misc]
    """
    Regra: Calcula se o ritmo atual de gastos (burn-rate) vai estourar o orçamento antes do fim do mês.
    """

    def __init__(self, days_threshold: int = 5):
        """
        Args:
            days_threshold: Número de dias mínimos decorridos no mês para começar a projetar.
        """
        self.days_threshold = days_threshold

    @property
    def rule_name(self) -> str:
        return "burn_rate_alert"

    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame,
        user_profile: dict[str, Any],
    ) -> RuleResult:
        now = datetime.now()
        current_day = now.day
        days_in_month = pd.Period(now.strftime("%Y-%m")).days_in_month

        if current_day < self.days_threshold:
            return RuleResult(triggered=False)

        if budgets_df.empty:
            return RuleResult(triggered=False)

        alerts = []
        for _, row in budgets_df.iterrows():
            categoria = row[config.ColunasOrcamentos.CATEGORIA]
            limite = (
                float(row[config.ColunasOrcamentos.LIMITE])
                if pd.notnull(row[config.ColunasOrcamentos.LIMITE])
                else 0.0
            )
            realizado = (
                float(row[config.ColunasOrcamentos.GASTO])
                if pd.notnull(row[config.ColunasOrcamentos.GASTO])
                else 0.0
            )

            if limite <= 0 or realizado <= 0:
                continue

            # Projeção linear: (gasto atual / dia atual) * total de dias no mês
            projetado = (realizado / current_day) * days_in_month

            if projetado > limite:
                percent_over = (projetado / limite - 1) * 100
                msg = (
                    f"📈 No ritmo atual, você gastará R$ {projetado:.2f} em *{categoria}* este mês, "
                    f"excedendo seu limite de R$ {limite:.2f} em {percent_over:.1f}%."
                )
                alerts.append(msg)

        if alerts:
            full_msg = "⚠️ **Alerta de Projeção de Gastos**\n\n" + "\n".join(alerts)
            return RuleResult(
                triggered=True,
                message_template=full_msg,
                priority=NotificationPriority.MEDIUM,
                category="burn_rate",
            )

        return RuleResult(triggered=False)
