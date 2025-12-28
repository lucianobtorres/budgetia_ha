
from abc import ABC, abstractmethod

class NotificationProvider(ABC):
    """
    Interface base para provedores de notificação (Telegram, WhatsApp, etc).
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @abstractmethod
    def send(self, recipient: str, message: str) -> bool:
        """
        Envia uma mensagem para o destinatário.
        Args:
            recipient: O ID/Telefone/Email do destinatário.
            message: O conteúdo da mensagem.
        Returns:
            True se enviado com sucesso (ou enfileirado), False caso contrário.
        """
        pass
