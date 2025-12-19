
from typing import Any
from app.notifications.channels.base_channel import INotificationChannel
from app.notifications.models.notification_message import NotificationMessage
from app.notifications.providers.whatsapp_provider import WhatsAppProvider

class WhatsAppChannel(INotificationChannel):
    def __init__(self):
        self.provider = WhatsAppProvider()

    @property
    def channel_name(self) -> str:
        return "whatsapp"

    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        # O Provider é sincrono por enquanto (Mock), mas a interface é async
        # Num cenário real Twilio, seria async ou thread pool
        try:
            return self.provider.send(recipient_id, message.text)
        except Exception as e:
            print(f"ERRO (WhatsAppChannel): {e}")
            return False

    def is_configured_for_user(self, user_config: dict[str, Any]) -> bool:
        return bool(self.get_recipient_id(user_config))

    def get_recipient_id(self, user_config: dict[str, Any]) -> str | None:
        return user_config.get("comunicacao", {}).get("whatsapp_phone")
