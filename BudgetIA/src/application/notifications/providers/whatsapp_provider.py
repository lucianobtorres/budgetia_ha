from core.logger import get_logger

from .base_provider import NotificationProvider

logger = get_logger("WhatsAppProvider")


class WhatsAppProvider(NotificationProvider):
    @property
    def name(self) -> str:
        return "whatsapp"

    def send(self, recipient: str, message: str) -> bool:
        # Aqui entraria a chamada para Twilio ou Meta API
        # Por enquanto, logamos a intenção
        logger.info(f"[MOCK] To: {recipient} | Msg: {message}")
        return True
