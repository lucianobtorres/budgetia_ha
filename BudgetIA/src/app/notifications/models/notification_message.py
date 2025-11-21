# src/app/notifications/models/notification_message.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class NotificationPriority(Enum):
    """Níveis de prioridade para notificações."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationMessage:
    """
    DTO para mensagens de notificação formatadas.
    Agnóstico de canal - cada canal interpreta a seu modo.
    """

    text: str
    priority: NotificationPriority
    category: str  # Ex: "financial_alert", "reminder", "insight"
    action_buttons: list[str] | None = None  # Para canais que suportam (Telegram, etc.)
    expires_at: datetime | None = None  # Para notificações temporárias
