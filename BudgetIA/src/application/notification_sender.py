# src/app/notification_sender.py
from telegram import Bot
from core.logger import get_logger

logger = get_logger("TelegramSender")


class TelegramSender:
    """
    Uma classe simples e dedicada para enviar mensagens
    proativas via Telegram.
    """

    def __init__(self, token: str):
        if not token:
            raise ValueError("Token do Telegram não fornecido.")
        self.bot = Bot(token=token)

    async def send_message(self, chat_id: str, message_text: str) -> bool:
        """
        Envia uma mensagem de texto para um chat_id específico.
        """
        if not chat_id:
            logger.error("chat_id está vazio. Não é possível enviar.")
            return False

        try:
            logger.info(
                f"Enviando: '{message_text}' para o chat_id: {chat_id}"
            )
            await self.bot.send_message(chat_id=chat_id, text=message_text)
            logger.info("Mensagem enviada com sucesso.")
            return True
        except Exception as e:
            logger.critical(f"Erro CRÍTICO ao enviar mensagem: {e}")
            return False
