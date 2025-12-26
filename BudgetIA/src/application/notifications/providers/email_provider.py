
from .base_provider import NotificationProvider

class EmailProvider(NotificationProvider):
    @property
    def name(self) -> str:
        return "email"

    def send(self, recipient: str, message: str) -> bool:
        # Aqui entraria SMTP ou SendGrid
        print(f"--- [Email MOCK] To: {recipient} | Subject: Alerta BudgetIA | Body: {message} ---")
        return True
