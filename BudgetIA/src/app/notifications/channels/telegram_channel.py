# src/app/notifications/channels/telegram_channel.py
import os
from typing import Any

from telegram import Bot

from app.notifications.channels.base_channel import INotificationChannel
from app.notifications.models.notification_message import NotificationMessage


class TelegramChannel(INotificationChannel):
    """
    Canal de notificação via Telegram.
    Implementa envio de mensagens através do Telegram Bot API.
    """

    def __init__(self, token: str | None = None):
        """
        Inicializa o canal Telegram.

        Args:
            token: Token do bot do Telegram. Se None, busca de TELEGRAM_TOKEN env var.

        Raises:
            ValueError: Se o token não for fornecido nem encontrado no ambiente.
        """
        self._token = token or os.getenv("TELEGRAM_TOKEN")
        if not self._token:
            raise ValueError(
                "Token do Telegram não fornecido e TELEGRAM_TOKEN não encontrado no .env"
            )
        self.bot = Bot(token=self._token)

    @property
    def channel_name(self) -> str:
        return "telegram"

    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        """
        Envia notificação via Telegram.

        Args:
            recipient_id: Chat ID do Telegram.
            message: NotificationMessage formatada.

        Returns:
            True se enviado com sucesso, False caso contrário.
        """
        if not recipient_id:
            print(
                "ERRO (TelegramChannel): recipient_id está vazio. Não é possível enviar."
            )
            return False

        try:
            print(
                f"--- (TelegramChannel) Enviando: '{message.text[:50]}...' para chat_id: {recipient_id} ---"
            )
            await self.bot.send_message(chat_id=recipient_id, text=message.text)
            print("--- (TelegramChannel) Mensagem enviada com sucesso. ---")
            return True
        except Exception as e:
            print(f"ERRO CRÍTICO (TelegramChannel) ao enviar mensagem: {e}")
            return False

    def is_configured_for_user(self, user_config: dict[str, Any]) -> bool:
        """
        Verifica se o usuário tem Telegram configurado.

        Args:
            user_config: Configuração do usuário.

        Returns:
            True se telegram_chat_id existe, False caso contrário.
        """
        comms_config = user_config.get("comunicacao", {})
        return bool(comms_config.get("telegram_chat_id"))

    def get_recipient_id(self, user_config: dict[str, Any]) -> str | None:
        """
        Extrai o chat_id do Telegram da configuração.

        Args:
            user_config: Configuração do usuário.

        Returns:
            Chat ID do Telegram ou None.
        """
        comms_config = user_config.get("comunicacao", {})
        return comms_config.get("telegram_chat_id")
