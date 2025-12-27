
from .base_provider import NotificationProvider

class WhatsAppProvider(NotificationProvider):
    @property
    def name(self) -> str:
        return "whatsapp"

    def send(self, recipient: str, message: str) -> bool:
        # Aqui entraria a chamada para Twilio ou Meta API
        # Por enquanto, logamos a intenção
        print(f"--- [WhatsApp MOCK] To: {recipient} | Msg: {message} ---")
        return True
