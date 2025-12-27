# src/app/notifications/models/rule_result.py
from dataclasses import dataclass
from typing import Any

from application.notifications.models.notification_message import (
    NotificationMessage,
    NotificationPriority,
)


@dataclass
class RuleResult:
    """
    Resultado da execução de uma regra de negócio.
    Contém template + contexto para gerar a mensagem final.
    """

    triggered: bool
    message_template: str = ""
    context: dict[str, Any] | None = None
    priority: NotificationPriority = NotificationPriority.LOW
    category: str = "financial_alert"

    def to_message(self) -> NotificationMessage:
        """
        Converte o template + context em uma NotificationMessage pronta.

        Returns:
            NotificationMessage formatada.
        """
        ctx = self.context or {}
        formatted_text = self.message_template.format(**ctx)
        return NotificationMessage(
            text=formatted_text,
            priority=self.priority,
            category=self.category,
        )
