from fastapi import APIRouter, Depends
from interfaces.api.dependencies import get_planilha_manager
from finance.planilha_manager import PlanilhaManager

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check() -> dict[str, str]:
    """Verifica se a API está online."""
    return {"status": "ok", "app": "BudgetIA API"}

@router.get("/readiness")
def readiness_check(manager: PlanilhaManager = Depends(get_planilha_manager)) -> dict[str, str]:
    """
    Verifica se a API consegue conectar com a Planilha/Banco.
    Se o manager falhar em carregar, o dependency injection vai falhar antes.
    """
    try:
        # Tenta uma operação leve para ver se o arquivo está acessível
        # O método check_connection já existe no Manager
        is_ok, msg = manager.check_connection()
        if is_ok:
            return {"status": "ready", "details": msg}
        else:
            return {"status": "error", "details": msg}
    except Exception as e:
        return {"status": "error", "details": str(e)}
