
from typing import Any
from application.notifications.channels.base_channel import INotificationChannel
from application.notifications.models.notification_message import NotificationMessage
from application.notifications.providers.whatsapp_provider import WhatsAppProvider
from core.logger import get_logger

logger = get_logger("WhatsAppChannel")

class WhatsAppChannel(INotificationChannel): # type: ignore[misc]
    def __init__(self) -> None:
        self.provider = WhatsAppProvider()

    @property
    def channel_name(self) -> str:
        return "whatsapp"

    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        # O Provider é sincrono por enquanto (Mock), mas a interface é async
        # Num cenário real Twilio, seria async ou thread pool
        try:
            return self.provider.send(recipient_id, message.text) # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"{e}")
            return False

    def is_configured_for_user(self, user_config: dict[str, Any]) -> bool:
        return bool(self.get_recipient_id(user_config))

    def get_recipient_id(self, user_config: dict[str, Any]) -> str | None:
        return user_config.get("comunicacao", {}).get("whatsapp_phone") # type: ignore[no-any-return]
