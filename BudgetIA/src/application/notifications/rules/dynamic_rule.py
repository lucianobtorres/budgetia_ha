
from typing import Any, Literal

import pandas as pd
from application.notifications.models.rule_result import RuleResult
from application.notifications.rules.base_rule import IFinancialRule
from application.notifications.models.notification_message import NotificationPriority


class DynamicThresholdRule(IFinancialRule): # type: ignore[misc]
    """
    Regra dinâmica configurável pelo usuário para monitorar gastos.
    Ex: "Avise se eu gastar mais de 500 em Jogos este mês".
    """

    def __init__(
        self,
        rule_id: str,
        category: str,
        threshold: float,
        period: Literal["monthly", "weekly"] = "monthly",
        custom_message: str | None = None,
    ):
        self.id = rule_id
        self.category = category
        self.threshold = threshold
        self.period = period
        self.custom_message = custom_message

    @property
    def rule_name(self) -> str:
        return f"dynamic_threshold_{self.id}"

    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame,
        user_profile: dict[str, Any],
    ) -> RuleResult:
        if transactions_df.empty:
            return RuleResult(triggered=False)

        # Filtrar por categoria (Case insensitive)
        # Assumindo que o DF tem coluna 'Categoria' e 'Valor' e 'Data'
        # Ajustar nomes de colunas conforme padrão do projeto (ColunasTransacoes?)
        # Vou usar nomes literais por enquanto e depois ajustamos se necessário, mas o ideal seria importar config.
        
        # Copia para não alterar original
        df = transactions_df.copy()
        
        # Normaliza categoria
        mask_cat = df["Categoria"].astype(str).str.lower() == self.category.lower()
        if not mask_cat.any():
            return RuleResult(triggered=False)
            
        filtered_df = df[mask_cat]

        # Filtrar por período (Mês atual vs Semana atual)
        # Assumindo coluna 'Data' como datetime
        if not pd.api.types.is_datetime64_any_dtype(filtered_df["Data"]):
             filtered_df["Data"] = pd.to_datetime(filtered_df["Data"], errors='coerce')

        now = pd.Timestamp.now()
        
        if self.period == "monthly":
            mask_period = (
                (filtered_df["Data"].dt.month == now.month) & 
                (filtered_df["Data"].dt.year == now.year)
            )
        elif self.period == "weekly":
            # Semana atual ISO
            mask_period = (
                (filtered_df["Data"].dt.isocalendar().week == now.isocalendar().week) &
                (filtered_df["Data"].dt.isocalendar().year == now.isocalendar().year)
            )
        else:
            mask_period = pd.Series([True] * len(filtered_df)) # type: ignore[unreachable]

        current_total = filtered_df[mask_period]["Valor"].sum()

        if current_total > self.threshold:
            diff = current_total - self.threshold
            msg = self.custom_message or (
                f"🚨 Alerta de Gasto: Você excedeu o limite de R$ {self.threshold:.2f} "
                f"em '{self.category}' ({self.period}). Total: R$ {current_total:.2f}."
            )
            
            return RuleResult(
                triggered=True,
                message_template=msg,
                context={
                    "category": self.category,
                    "limit": self.threshold,
                    "current": current_total,
                    "diff": diff
                },
                priority=NotificationPriority.HIGH
            )

        return RuleResult(triggered=False)

    def to_dict(self) -> dict[str, Any]:
        """Serializa a regra para salvar em JSON."""
        return {
            "id": self.id,
            "type": "threshold",
            "category": self.category,
            "threshold": self.threshold,
            "period": self.period,
            "custom_message": self.custom_message
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DynamicThresholdRule":
        return cls(
            rule_id=data["id"],
            category=data["category"],
            threshold=data["threshold"],
            period=data.get("period", "monthly"),
            custom_message=data.get("custom_message")
        )
