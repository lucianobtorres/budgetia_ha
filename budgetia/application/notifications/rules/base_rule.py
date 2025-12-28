# src/app/notifications/rules/base_rule.py
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from application.notifications.models.rule_result import RuleResult


class IFinancialRule(ABC):
    """
    Interface abstrata para regras de negócio financeiras.
    Cada regra verifica uma condição específica e retorna se deve notificar.

    Responsabilidade Única: Detectar violações de regras financeiras.
    Sem dependências de infraestrutura (canais, configuração, etc.).
    """

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """
        Nome único da regra para identificação e logs.

        Returns:
            Nome identificador (ex: "transport_missing", "budget_overage").
        """
        pass

    @abstractmethod
    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame,
        user_profile: dict[str, Any],
    ) -> RuleResult:
        """
        Verifica se a regra foi violada e deve gerar notificação.

        Args:
            transactions_df: DataFrame com transações do usuário.
            budgets_df: DataFrame com orçamentos configurados.
            user_profile: Dicionário com perfil financeiro do usuário.

        Returns:
            RuleResult com:
            - triggered=True se deve notificar, False caso contrário
            - message_template: Template da mensagem com placeholders {var}
            - context: Dicionário para interpolar no template
            - priority: Nível de prioridade da notificação
        """
        pass
