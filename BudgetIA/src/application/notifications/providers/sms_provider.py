
from .base_provider import NotificationProvider

class SMSProvider(NotificationProvider):
    @property
    def name(self) -> str:
        return "sms"

    def send(self, recipient: str, message: str) -> bool:
        # Aqui entraria Twilio SMS
        print(f"--- [SMS MOCK] To: {recipient} | Msg: {message} ---")
        return True
