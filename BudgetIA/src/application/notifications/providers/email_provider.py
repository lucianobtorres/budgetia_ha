from core.logger import get_logger

from .base_provider import NotificationProvider

logger = get_logger("EmailProvider")


class EmailProvider(NotificationProvider):
    @property
    def name(self) -> str:
        return "email"

    def send(self, recipient: str, message: str) -> bool:
        # Aqui entraria SMTP ou SendGrid
        logger.info(
            f"[MOCK] To: {recipient} | Subject: Alerta BudgetIA | Body: {message}"
        )
        return True
