from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from interfaces.api.dependencies import get_notification_service
from application.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationModel(BaseModel):
    id: str
    timestamp: str
    message: str
    category: str
    priority: str
    read: bool


@router.get("/", response_model=list[NotificationModel])
def listar_notificacoes(
    unread_only: bool = True,
    service: NotificationService = Depends(get_notification_service)
) -> list[dict[str, Any]]:
    """Retorna lista de notificações do usuário."""
    return service.get_notifications(unread_only=unread_only) # type: ignore[no-any-return]


@router.post("/{notification_id}/read")
def marcar_como_lida(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service)
) -> dict[str, str]:
    """Marca uma notificação específica como lida."""
    success = service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return {"status": "success"}


@router.delete("/{notification_id}")
def excluir_notificacao(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service)
) -> dict[str, str]:
    """Exclui uma notificação permanentemente."""
    success = service.delete_notification(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return {"status": "success"}


@router.post("/read-all")
def marcar_todas_lidas(
    service: NotificationService = Depends(get_notification_service)
) -> dict[str, str]:
    """Marca todas as notificações como lidas."""
    service.mark_all_as_read()
    return {"status": "success"}


# --- PUSH NOTIFICATIONS ---

from application.services.push_notification_service import PushNotificationService
from application.notifications.models.push_subscription import PushSubscription
from interfaces.api.dependencies import get_push_notification_service

class SubscriptionInput(BaseModel):
    endpoint: str
    keys: dict[str, str] # { p256dh: str, auth: str }
    
    
@router.post("/subscribe")
def subscribe_push(
    subscription: SubscriptionInput,
    service: PushNotificationService = Depends(get_push_notification_service),
    user_config: Any = Depends(get_notification_service) # Just to hack getting user_id if needed, but push_service handles it
) -> dict[str, str]:
    """Registra uma nova subscrição Push."""
    # Extrair chaves
    keys = subscription.keys
    
    # Criar modelo (Assume user_id do contexto de config service que o push service já tem acesso? Não, o endpoint não sabe user_id sem context)
    # Pegando user_id do service de notificação (que tem config)
    user_id = user_config.config_service.username
    
    sub = PushSubscription(
        endpoint=subscription.endpoint,
        keys_auth=keys.get("auth", ""),
        keys_p256dh=keys.get("p256dh", ""),
        user_id=user_id,
        device_name="Browser"
    )
    
    service.subscribe(sub)
    return {"status": "subscribed"}


@router.post("/unsubscribe")
def unsubscribe_push(
    endpoint: str,
    service: PushNotificationService = Depends(get_push_notification_service)
) -> dict[str, str]:
    """Remove subscrição."""
    service.unsubscribe(endpoint)
    return {"status": "unsubscribed"}


@router.post("/test-push")
def test_push(
    service: PushNotificationService = Depends(get_push_notification_service),
    user_config: Any = Depends(get_notification_service)
) -> dict[str, str]:
    """Envia notificação de teste."""
    user_id = user_config.config_service.username
    count = service.send_notification(user_id, "Testando Push Notification! 🚀", "BudgetIA")
    return {"status": "sent", "count": str(count)}
