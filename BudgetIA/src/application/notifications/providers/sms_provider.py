from core.logger import get_logger

from .base_provider import NotificationProvider

logger = get_logger("SMSProvider")


class SMSProvider(NotificationProvider):
    @property
    def name(self) -> str:
        return "sms"

    def send(self, recipient: str, message: str) -> bool:
        # Aqui entraria Twilio SMS
        logger.info(f"[MOCK] To: {recipient} | Msg: {message}")
        return True
