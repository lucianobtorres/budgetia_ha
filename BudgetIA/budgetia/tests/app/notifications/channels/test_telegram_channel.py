# tests/app/notifications/channels/test_telegram_channel.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.notifications.channels.telegram_channel import TelegramChannel
from application.notifications.models.notification_message import (
    NotificationMessage,
    NotificationPriority,
)


class TestTelegramChannel:
    """Testes para o canal de notificação Telegram."""

    def test_channel_name(self):
        """Testa se o nome do canal está correto."""
        with patch("os.getenv", return_value="fake_token"):
            channel = TelegramChannel()
            assert channel.channel_name == "telegram"

    def test_init_with_token(self):
        """Testa inicialização com token fornecido."""
        channel = TelegramChannel(token="test_token_123")
        assert channel._token == "test_token_123"

    def test_init_with_env_var(self):
        """Testa inicialização com token do ambiente."""
        with patch("os.getenv", return_value="env_token_456"):
            channel = TelegramChannel()
            assert channel._token == "env_token_456"

    def test_init_without_token_raises_error(self):
        """Testa se erro é levantado quando token não está disponível."""
        with patch("os.getenv", return_value=None):
            with pytest.raises(ValueError, match="Token do Telegram"):
                TelegramChannel()

    def test_is_configured_for_user_with_chat_id(self):
        """Testa verificação de configuração quando chat_id existe."""
        channel = TelegramChannel(token="test_token")

        user_config = {"comunicacao": {"telegram_chat_id": "123456789"}}

        assert channel.is_configured_for_user(user_config) is True

    def test_is_configured_for_user_without_chat_id(self):
        """Testa verificação de configuração quando chat_id não existe."""
        channel = TelegramChannel(token="test_token")

        user_config = {"comunicacao": {}}

        assert channel.is_configured_for_user(user_config) is False

    def test_is_configured_for_user_without_comunicacao(self):
        """Testa verificação sem seção 'comunicacao'."""
        channel = TelegramChannel(token="test_token")

        user_config = {}

        assert channel.is_configured_for_user(user_config) is False

    def test_get_recipient_id(self):
        """Testa extração do recipient_id."""
        channel = TelegramChannel(token="test_token")

        user_config = {"comunicacao": {"telegram_chat_id": "987654321"}}

        recipient_id = channel.get_recipient_id(user_config)
        assert recipient_id == "987654321"

    def test_get_recipient_id_missing(self):
        """Testa extração quando chat_id não existe."""
        channel = TelegramChannel(token="test_token")

        user_config = {"comunicacao": {}}

        recipient_id = channel.get_recipient_id(user_config)
        assert recipient_id is None

    @pytest.mark.asyncio
    async def test_send_success(self):
        """Testa envio bem-sucedido de mensagem."""
        channel = TelegramChannel(token="test_token")

        # Mock do bot
        channel.bot = MagicMock()
        channel.bot.send_message = AsyncMock(return_value=True)

        message = NotificationMessage(
            text="Teste de mensagem",
            priority=NotificationPriority.HIGH,
            category="test",
        )

        result = await channel.send("123456", message)

        assert result is True
        channel.bot.send_message.assert_called_once_with(
            chat_id="123456", text="Teste de mensagem"
        )

    @pytest.mark.asyncio
    async def test_send_empty_recipient_id(self):
        """Testa envio com recipient_id vazio."""
        channel = TelegramChannel(token="test_token")

        message = NotificationMessage(
            text="Teste",
            priority=NotificationPriority.LOW,
            category="test",
        )

        result = await channel.send("", message)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_telegram_api_error(self):
        """Testa tratamento de erro da API do Telegram."""
        channel = TelegramChannel(token="test_token")

        # Mock do bot para simular erro
        channel.bot = MagicMock()
        channel.bot.send_message = AsyncMock(
            side_effect=Exception("Telegram API Error")
        )

        message = NotificationMessage(
            text="Teste de mensagem",
            priority=NotificationPriority.MEDIUM,
            category="test",
        )

        result = await channel.send("123456", message)

        assert result is False
