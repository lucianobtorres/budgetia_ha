
from .base_provider import NotificationProvider
from core.logger import get_logger

logger = get_logger("EmailProvider")

class EmailProvider(NotificationProvider):
    @property
    def name(self) -> str:
        return "email"

    def send(self, recipient: str, message: str) -> bool:
        # Aqui entraria SMTP ou SendGrid
        logger.info(f"[MOCK] To: {recipient} | Subject: Alerta BudgetIA | Body: {message}")
        return True
