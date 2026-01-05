from typing import Any, Optional
import os
from twilio.rest import Client

from application.notifications.channels.base_channel import INotificationChannel
from application.notifications.models.notification_message import NotificationMessage
from core.logger import get_logger

logger = get_logger("WhatsAppChannel")

class WhatsAppChannel(INotificationChannel):
    """
    Canal de notificação via WhatsApp (usando Twilio API).
    """
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "whatsapp:+14155238886") # Sandbox Default
        
        if not self.account_sid or not self.auth_token:
            logger.warning("Credenciais do Twilio não configuradas. WhatsAppChannel desativado.")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                 logger.error(f"Erro ao inicializar cliente Twilio: {e}")
                 self.client = None

    @property
    def channel_name(self) -> str:
        return "whatsapp"

    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        if not self.client:
            logger.debug("Tentativa de envio sem cliente Twilio configurado (Mock/Skipped).")
            return False

        # Formata o número (Adiciona prefixo whatsapp: se não tiver)
        if not recipient_id.startswith("whatsapp:"):
            recipient_id = f"whatsapp:{recipient_id}"

        # Tenta usar title se existir, senão só text
        title = getattr(message, "title", "Notificação")
        text = getattr(message, "text", str(message))
        
        full_message = f"*{title}*\n\n{text}"

        try:
            logger.info(f"Enviando WhatsApp para {recipient_id}")
            msg = self.client.messages.create(
                from_=self.from_number,
                body=full_message,
                to=recipient_id
            )
            logger.debug(f"WhatsApp enviado: SID={msg.sid}")
            return True
        except Exception as e:
            logger.error(f"Falha ao enviar WhatsApp: {e}")
            return False

    def is_configured_for_user(self, user_config: dict[str, Any]) -> bool:
        return bool(self.get_recipient_id(user_config))
