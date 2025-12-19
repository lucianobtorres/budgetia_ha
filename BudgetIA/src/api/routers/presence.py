from fastapi import APIRouter, Depends

from api.dependencies import get_presence_service, get_user_config_service
from app.services.presence_service import PresenceService
from core.user_config_service import UserConfigService

router = APIRouter(prefix="/presence", tags=["Presence"])

@router.post("/heartbeat")
def send_heartbeat(
    presence_service: PresenceService = Depends(get_presence_service),
    config_service: UserConfigService = Depends(get_user_config_service)
):
    """Atualiza o 'visto por último' do usuário."""
    presence_service.update_heartbeat(config_service.username)
    return {"status": "ok"}

@router.get("/toasts")
def get_toasts(
    presence_service: PresenceService = Depends(get_presence_service),
    config_service: UserConfigService = Depends(get_user_config_service)
):
    """Recupera notificações instantâneas (Toasts) e limpa a fila."""
    toasts = presence_service.pop_toasts(config_service.username)
    return toasts
