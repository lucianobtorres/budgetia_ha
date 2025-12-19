
from typing import Any
from app.notifications.channels.base_channel import INotificationChannel
from app.notifications.models.notification_message import NotificationMessage
from app.notifications.providers.sms_provider import SMSProvider

class SMSChannel(INotificationChannel):
    def __init__(self):
        self.provider = SMSProvider()

    @property
    def channel_name(self) -> str:
        return "sms"

    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        try:
            return self.provider.send(recipient_id, message.text)
        except Exception as e:
            print(f"ERRO (SMSChannel): {e}")
            return False

    def is_configured_for_user(self, user_config: dict[str, Any]) -> bool:
        return bool(self.get_recipient_id(user_config))

    def get_recipient_id(self, user_config: dict[str, Any]) -> str | None:
        return user_config.get("comunicacao", {}).get("sms_phone")
