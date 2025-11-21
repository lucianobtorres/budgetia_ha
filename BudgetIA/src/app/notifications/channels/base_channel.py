# src/app/notifications/channels/base_channel.py
from abc import ABC, abstractmethod
from typing import Any

from app.notifications.models.notification_message import NotificationMessage


class INotificationChannel(ABC):
    """
    Interface abstrata para canais de entrega de notificações.
    Cada canal implementa sua própria lógica de envio.

    Responsabilidade Única: Enviar notificações através de um canal específico.
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """
        Nome único do canal para identificação.

        Returns:
            Nome do canal (ex: "telegram", "whatsapp", "in_app").
        """
        pass

    @abstractmethod
    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        """
        Envia uma notificação através deste canal.

        Args:
            recipient_id: ID do destinatário no canal (ex: chat_id do Telegram).
            message: NotificationMessage com conteúdo formatado.

        Returns:
            True se enviado com sucesso, False se falhou.
        """
        pass

    @abstractmethod
    def is_configured_for_user(self, user_config: dict[str, Any]) -> bool:
        """
        Verifica se este canal está configurado para o usuário.

        Args:
            user_config: Dicionário de configuração do usuário.

        Returns:
            True se o canal pode ser usado, False caso contrário.
        """
        pass

    def get_recipient_id(self, user_config: dict[str, Any]) -> str | None:
        """
        Extrai o ID do destinatário da configuração do usuário.

        Args:
            user_config: Dicionário de configuração do usuário.

        Returns:
            ID do destinatário ou None se não configurado.
        """
        comms_config = user_config.get("comunicacao", {})
        # Cada subclasse deve sobrescrever se usar formato diferente
        return comms_config.get(f"{self.channel_name}_chat_id")
