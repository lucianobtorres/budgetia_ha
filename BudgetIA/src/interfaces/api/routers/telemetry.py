from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from interfaces.api.dependencies import get_user_config_service
from core.user_config_service import UserConfigService
from core.behavior.user_behavior_service import UserBehaviorService

from core.logger import get_logger

logger = get_logger("API_Telemetry")

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

class TelemetryAction(BaseModel):
    action_type: str
    metadata: Optional[Dict[str, Any]] = None

class RuleFeedback(BaseModel):
    rule_name: str
    feedback_type: str # 'ignored', 'dismissed', 'clicked', 'positive'

@router.post("/action")
def log_action(
    action: TelemetryAction,
    config_service: UserConfigService = Depends(get_user_config_service)
):
    """
    Registra uma ação genérica do usuário para análise de comportamento.
    Ex: 'view_dashboard', 'open_drawer_budgets', 'filter_transactions'
    """
    try:
        service = UserBehaviorService(config_service.username)
        service.log_action(action.action_type, action.metadata)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"ERRO TELEMETRY: {e}")
        # Telemetria não deve quebrar a aplicação, mas reportamos erro 500 para debug
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
def log_feedback(
    feedback: RuleFeedback,
    config_service: UserConfigService = Depends(get_user_config_service)
):
    """
    Registra feedback sobre uma regra/notificação específica.
    Fundamental para o 'Learning' do sistema.
    """
    try:
        service = UserBehaviorService(config_service.username)
        service.log_rule_feedback(feedback.rule_name, feedback.feedback_type)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"ERRO TELEMETRY FEEDBACK: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tours")
def get_seen_tours(
    config_service: UserConfigService = Depends(get_user_config_service)
):
    """
    Retorna a lista de tours que o usuário já completou/dispensou.
    Usado para sincronizar estado entre dispositivos.
    """
    try:
        service = UserBehaviorService(config_service.username)
        return {"seen_tours": service.get_seen_tours()}
    except Exception as e:
        logger.error(f"ERRO TELEMETRY TOURS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tours/{tour_id}")
def mark_tour_seen(
    tour_id: str,
    config_service: UserConfigService = Depends(get_user_config_service)
):
    """
    Marca um tour como visto no servidor.
    """
    try:
        service = UserBehaviorService(config_service.username)
        service.mark_tour_seen(tour_id)
        return {"status": "ok", "tour_id": tour_id}
    except Exception as e:
        logger.error(f"ERRO TELEMETRY MARK TOUR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tours")
def reset_tours(
    config_service: UserConfigService = Depends(get_user_config_service)
):
    """
    Reseta o histórico de tours do usuário.
    """
    try:
        service = UserBehaviorService(config_service.username)
        service.reset_tours()
        return {"status": "ok", "message": "Tours resetados com sucesso"}
    except Exception as e:
        logger.error(f"ERRO TELEMETRY RESET TOURS: {e}")
        raise HTTPException(status_code=500, detail=str(e))
