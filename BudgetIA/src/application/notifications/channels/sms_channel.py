
from typing import Any
from application.notifications.channels.base_channel import INotificationChannel
from application.notifications.models.notification_message import NotificationMessage
from application.notifications.providers.sms_provider import SMSProvider
from core.logger import get_logger

logger = get_logger("SMSChannel")

class SMSChannel(INotificationChannel): # type: ignore[misc]
    def __init__(self) -> None:
        self.provider = SMSProvider()

    @property
    def channel_name(self) -> str:
        return "sms"

    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        try:
            return self.provider.send(recipient_id, message.text) # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"{e}")
            return False

    def is_configured_for_user(self, user_config: dict[str, Any]) -> bool:
        return bool(self.get_recipient_id(user_config))

    def get_recipient_id(self, user_config: dict[str, Any]) -> str | None:
        return user_config.get("comunicacao", {}).get("sms_phone") # type: ignore[no-any-return]
