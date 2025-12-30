from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.dependencies import get_planilha_manager, get_user_config_service, get_llm_orchestrator
from finance.planilha_manager import PlanilhaManager
from core.user_config_service import UserConfigService
from core.llm_manager import LLMOrchestrator
from application.proactive_jobs import run_proactive_notifications
from core.logger import get_logger

logger = get_logger("API_Jobs")

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/run")
async def run_proactive_job(
    manager: PlanilhaManager = Depends(get_planilha_manager),
    config_service: UserConfigService = Depends(get_user_config_service),
    llm_orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)
) -> dict[str, Any]:
    """
    Executa os jobs proativos para o usuário atual (definido pelo Header X-User-ID).
    Isso garante que o job use a MESMA instância de PlanilhaManager que a API/Chat.
    """
    try:
        if not manager:
            raise HTTPException(status_code=500, detail="PlanilhaManager não disponível.")
            
        logger.info(f"Executando job proativo para {config_service.username}...")
        
        result = await run_proactive_notifications(
            config_service=config_service,
            llm_orchestrator=llm_orchestrator,
            plan_manager=manager
        )
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"ERRO API JOB: {e}")
        raise HTTPException(status_code=500, detail=str(e))
