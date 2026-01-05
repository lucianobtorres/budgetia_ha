from datetime import timedelta, datetime
import pandas as pd
from typing import Any

from application.notifications.rules.base_rule import IFinancialRule
from application.notifications.models.rule_result import RuleResult
from application.notifications.models.notification_message import NotificationPriority

class RecurringExpenseMonitor(IFinancialRule):
    """
    Monitora despesas recorrentes e detecta variações anômalas de valor.
    Ex: Uma conta de luz que veio 20% mais cara que a média.
    """
    
    def __init__(self, days_lookback: int = 90, threshold_percent: float = 1.2):
        self.days_lookback = days_lookback
        self.threshold_percent = threshold_percent # 20% acima da média
        self.display_name = "Monitor de Gastos Recorrentes"

    @property
    def rule_name(self) -> str:
        return "recurring_expense_monitor"

    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame,
        user_profile: dict[str, Any],
    ) -> RuleResult:
        if transactions_df.empty:
            return RuleResult(triggered=False)

        # 1. Filtrar período de análise
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=self.days_lookback)
        df = transactions_df[transactions_df['Data'] >= cutoff_date].copy()
        
        if df.empty:
             return RuleResult(triggered=False)

        # 2. Agrupar por descrição (normalizada) para identificar recorrencia
        # Simplificação: agrupa pelo nome exato
        grouped = df.groupby('Descrição')['Valor'].agg(['count', 'mean', 'std', 'last'])
        
        # Considera recorrente se aparece pelo menos 3 vezes no periodo
        recurrent = grouped[grouped['count'] >= 3]
        
        anomalies = []
        
        for description, row in recurrent.iterrows():
            avg_val = row['mean']
            last_val = df[df['Descrição'] == description].iloc[-1]['Valor'] # Pega o valor da ultima ocorrencia real
            
            # Se o ultimo valor for muito maior que a média (ex: +20%)
            if last_val > (avg_val * self.threshold_percent):
                diff_percent = ((last_val - avg_val) / avg_val) * 100
                anomalies.append(f"{description}: R$ {last_val:.2f} (+{diff_percent:.0f}%)")

        if anomalies:
            return RuleResult(
                triggered=True,
                priority=NotificationPriority.MEDIUM,
                message_template="Detectamos variações em gastos recorrentes: {anomalies}",
                context={"anomalies": ", ".join(anomalies)}
            )

        return RuleResult(triggered=False)
