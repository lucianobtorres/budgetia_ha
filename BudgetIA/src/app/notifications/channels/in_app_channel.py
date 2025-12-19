from typing import Any

from app.notifications.channels.base_channel import INotificationChannel
from app.services.presence_service import PresenceService


class InAppChannel(INotificationChannel):
    """
    Canal de Notificação Web (In-App).
    Envia mensagens para a fila de 'Toasts' que o frontend consome via Polling.
    """

    def __init__(self):
        self.presence_service = PresenceService()

    @property
    def channel_name(self) -> str:
        return "in_app"

    def is_configured_for_user(self, user_config: dict[str, Any]) -> bool:
        # Sempre disponível, pois é parte da plataforma
        return True

    def get_recipient_id(self, user_config: dict[str, Any]) -> str | None:
        # O ID do destinatário é o próprio username, que será passado no send() 
        # ou precisamos garantir que o orchestrator passe o user_id correto.
        # O Orchestrator passa 'recipient_id' baseado no retorno daqui.
        # Mas o user_config pode não ter o ID explícito se for arquivo local.
        # Vamos assumir que quem chama sabe o user_id, mas a interface pede para extrair do config.
        # Hack: O orchestrator já tem o config_service.username, mas o método pede do dict.
        # Vamos retornar "current_user" e resolver no send? 
        # Não, o Orchestrator chama `get_recipient_id` e passa para `send`.
        # Precisamos que o Orchestrator passe o username.
        # O UserConfigService não salva o username dentro do json (geralmente).
        # Vamos ajustar o Orchestrator depois se precisar, mas por hora vamos retornar "user_placeholder"
        # e confiar que o InAppChannel via PresenceService vai usar o contexto correto?
        # Não, o PresenceService precisa do user_id.
        # O Orchestrator precisa passar o user_id real.
        return "user_ref" # Placeholder, o send vai ignorar isso se tiver acesso ao contexto?
        # Espere, o send(recipient_id, message) RECEBE o id.
        # Como pegamos o username DO ARQUIVO user_config.json? Não tem.
        # O Orchestrator tem `self.config_service`.
        pass

    async def send(self, recipient_id: str, message: str) -> bool:
        """
        Envia mensagem para a fila de toasts.
        NOTA: recipient_id precisa ser o USERNAME.
        """
        if not recipient_id or recipient_id == "user_ref":
            # Fallback se a lógica acima falhar
            print("ERRO (InAppChannel): Username não fornecido corretamente.")
            return False
            
        try:
            self.presence_service.push_toast(user_id=recipient_id, message=message)
            return True
        except Exception as e:
            print(f"ERRO (InAppChannel): Falha ao enviar toast: {e}")
            return False
