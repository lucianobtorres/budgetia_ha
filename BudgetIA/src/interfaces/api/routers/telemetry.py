from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from interfaces.api.dependencies import get_user_config_service
from core.user_config_service import UserConfigService
from core.behavior.user_behavior_service import UserBehaviorService

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
        print(f"ERRO TELEMETRY: {e}")
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
        print(f"ERRO TELEMETRY FEEDBACK: {e}")
        raise HTTPException(status_code=500, detail=str(e))
