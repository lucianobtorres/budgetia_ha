from typing import Any

import pandas as pd

import config
from application.notifications.models.notification_message import NotificationPriority
from application.notifications.models.rule_result import RuleResult
from application.notifications.rules.base_rule import IFinancialRule


class BudgetOverrunRule(IFinancialRule): # type: ignore[misc]
    """
    Regra: Detecta se alguma categoria excedeu X% do orçamento definido.
    """

    def __init__(self, threshold_percent: float = 0.9):
        """
        Args:
            threshold_percent: Porcentagem de alerta (0.9 = 90%).
        """
        self.threshold_percent = threshold_percent

    @property
    def rule_name(self) -> str:
        return "budget_overrun"

    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame,
        user_profile: dict[str, Any],
    ) -> RuleResult:
        """
        Verifica orçamentos estourados ou próximos de estourar.
        """
        print(f"LOG (BudgetOverrunRule): Verificando orçamentos acima de {self.threshold_percent*100}%...")

        if budgets_df.empty:
            print("LOG (BudgetOverrunRule): Tabela de orçamentos vazia.")
            return RuleResult(triggered=False)

        # Colunas esperadas: Categoria, Limite (Estimado), Gasto (Realizado)
        required_cols = [
            config.ColunasOrcamentos.CATEGORIA,
            config.ColunasOrcamentos.LIMITE,
            config.ColunasOrcamentos.GASTO,
        ]
        
        # Verifica colunas (case insensitive ou mapeamento direto se possível)
        # Assumindo que o DataFrame venha com os nomes corretos do config
        for col in required_cols:
            if col not in budgets_df.columns:
                print(f"ERRO (BudgetOverrunRule): Coluna '{col}' não encontrada em budgets_df.")
                return RuleResult(triggered=False)

        alerts = []

        for _, row in budgets_df.iterrows():
            categoria = row[config.ColunasOrcamentos.CATEGORIA]
            # LIMITE = Estimado
            estimado = float(row[config.ColunasOrcamentos.LIMITE]) if pd.notnull(row[config.ColunasOrcamentos.LIMITE]) else 0.0
            # GASTO = Realizado
            realizado = float(row[config.ColunasOrcamentos.GASTO]) if pd.notnull(row[config.ColunasOrcamentos.GASTO]) else 0.0

            if estimado <= 0:
                continue

            percent_used = realizado / estimado

            if percent_used >= self.threshold_percent:
                if percent_used > 1.0:
                    status = "ESTOURADO"
                    priority = NotificationPriority.HIGH
                    msg = f"URGENTE: Você estourou o orçamento de *{categoria}*! ({percent_used*100:.1f}%)"
                else:
                    status = "ALERTA"
                    priority = NotificationPriority.MEDIUM
                    msg = f"Atenção: Você já usou {percent_used*100:.1f}% do orçamento de *{categoria}*."
                
                alerts.append(msg)

        if alerts:
            # Junta alertas em uma mensagem
            full_msg = "🚨 **Alerta de Orçamento**\n\n" + "\n".join(alerts)
            return RuleResult(
                triggered=True,
                message_template=full_msg,
                priority=NotificationPriority.HIGH, # Pega a maior prioridade (simplificação)
                category="budget_alert"
            )

        return RuleResult(triggered=False)
