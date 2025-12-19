from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_notification_service
from app.services.notification_service import NotificationService

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
):
    """Retorna lista de notificações do usuário."""
    return service.get_notifications(unread_only=unread_only)


@router.post("/{notification_id}/read")
def marcar_como_lida(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """Marca uma notificação específica como lida."""
    success = service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return {"status": "success"}


@router.delete("/{notification_id}")
def excluir_notificacao(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """Exclui uma notificação permanentemente."""
    success = service.delete_notification(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return {"status": "success"}


@router.post("/read-all")
def marcar_todas_lidas(
    service: NotificationService = Depends(get_notification_service)
):
    """Marca todas as notificações como lidas."""
    service.mark_all_as_read()
    return {"status": "success"}
