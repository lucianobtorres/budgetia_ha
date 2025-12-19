
from typing import Any
from app.notifications.channels.base_channel import INotificationChannel
from app.notifications.models.notification_message import NotificationMessage
from app.notifications.providers.email_provider import EmailProvider

class EmailChannel(INotificationChannel):
    def __init__(self):
        self.provider = EmailProvider()

    @property
    def channel_name(self) -> str:
        return "email"

    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        try:
            return self.provider.send(recipient_id, message.text)
        except Exception as e:
            print(f"ERRO (EmailChannel): {e}")
            return False

    def is_configured_for_user(self, user_config: dict[str, Any]) -> bool:
        return bool(self.get_recipient_id(user_config))

    def get_recipient_id(self, user_config: dict[str, Any]) -> str | None:
        return user_config.get("comunicacao", {}).get("email_address")
