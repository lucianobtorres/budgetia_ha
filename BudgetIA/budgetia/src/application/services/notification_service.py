import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from core.user_config_service import UserConfigService


from application.services.push_notification_service import PushNotificationService

class NotificationService:
    """
    Serviço de persistência para notificações.
    Salva alertas em arquivo JSON para garantir que nunca se percam.
    """

    def __init__(self, config_service: UserConfigService, push_service: PushNotificationService | None = None):
        self.config_service = config_service
        self.user_dir = config_service.config_dir
        self.file_path = self.user_dir / "notifications.json"
        self.push_service = push_service
        
    def _load(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f) # type: ignore[no-any-return]
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, notifications: list[dict[str, Any]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(notifications, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"ERRO: Falha ao salvar notificações: {e}")

    def add_notification(self, message: str, category: str, priority: str) -> dict[str, Any]:
        """Cria e salva uma nova notificação."""
        notifications = self._load()
        
        new_notif = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "category": category,
            "priority": priority,
            "read": False
        }
        
        # Adiciona no INÍCIO da lista (mais recente primeiro)
        notifications.insert(0, new_notif)
        
        # Limite de segurança (últimas 100 notificações) para não explodir o disco
        if len(notifications) > 100:
            notifications = notifications[:100]
            
        self._save(notifications)
        
        # Tenta enviar Push Notification
        if self.push_service:
            # TODO: Obter user_id real se multi-usuário. Por enquanto usa current user do config.
            user_id = self.config_service.username
            
            # Map category to Title
            title_map = {
                'financial_reminder': 'Lembrete Financeiro',
                'financial_alert': 'Alerta Financeiro',
                'budget_exceeded': 'Orçamento Excedido',
                'insight': 'Insight Financeiro'
            }
            title = title_map.get(category, "BudgetIA")
            
            self.push_service.send_notification(
                user_id=user_id,
                message=message,
                title=title,
                tag=category
            )
            
        return new_notif

    def get_notifications(self, unread_only: bool = True) -> list[dict[str, Any]]:
        """Busca notificações."""
        all_notifs = self._load()
        if unread_only:
            return [n for n in all_notifs if not n.get("read", False)]
        return all_notifs

    def mark_as_read(self, notification_id: str) -> bool:
        """Marca uma notificação como lida."""
        notifications = self._load()
        found = False
        
        for n in notifications:
            if n["id"] == notification_id:
                n["read"] = True
                found = True
                break
        
        if found:
            self._save(notifications)
            
        return found

    def delete_notification(self, notification_id: str) -> bool:
        """Remove uma notificação permanentemente."""
        notifications = self._load()
        initial_len = len(notifications)
        notifications = [n for n in notifications if n["id"] != notification_id]
        
        if len(notifications) < initial_len:
            self._save(notifications)
            return True
        return False

    def mark_all_as_read(self) -> None:
        """Marca todas como lidas (Botão 'Limpar')."""
        notifications = self._load()
        for n in notifications:
            n["read"] = True
        self._save(notifications)
