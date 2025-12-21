from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Body
from api.dependencies import get_planilha_manager, get_user_config_service
from finance.planilha_manager import PlanilhaManager
from core.user_config_service import UserConfigService
from config import NomesAbas, PROFILE_DESIRED_FIELDS, ColunasPerfil

router = APIRouter(prefix="/profile", tags=["Perfil"])

@router.get("/")
def get_profile(
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> list[dict[str, Any]]:
    """
    Retorna os dados do perfil financeiro.
    """
    try:
        manager.ensure_profile_fields(PROFILE_DESIRED_FIELDS)
        df = manager.visualizar_dados(NomesAbas.PERFIL_FINANCEIRO)
        if df is None or df.empty:
            return []
        
        # Sanitização simples para JSON
        df = df.fillna("")
        return df.to_dict(orient="records") # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/bulk")
def update_profile_bulk(
    itens: list[dict[str, Any]] = Body(...),
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    """
    Atualiza o perfil.
    """
    try:
        if not itens:
            return {"message": "Nenhuma alteração enviada."}
            
        df_new = pd.DataFrame(itens)
        
        # Limpeza essencial
        if ColunasPerfil.CAMPO in df_new.columns:
            df_new = df_new.dropna(subset=[ColunasPerfil.CAMPO])
        
        manager.update_dataframe(NomesAbas.PERFIL_FINANCEIRO, df_new)
        manager.save()
        
        return {"message": "Perfil atualizado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar perfil: {e}")

# --- MEMORY (BRAIN) ENDPOINTS ---
from core.memory.memory_service import MemoryService
from api.dependencies import get_memory_service

@router.get("/memory")
def get_memory_facts(
    service: MemoryService = Depends(get_memory_service)
) -> list[dict[str, Any]]:
    """Retorna fatos aprendidos pela IA."""
    try:
        return service._load_memory()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/memory/{fact_content}")
def delete_memory_fact(
    fact_content: str,
    service: MemoryService = Depends(get_memory_service)
):
    """Esquece um fato específico."""
    try:
        # Nota: O endpoint receberá o content codificado na URL, mas FastAPI decodifica.
        # Precisamos garantir que removemos exatamente o conteúdo.
        service.forget_fact(fact_content)
        return {"message": "Fato esquecido."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- RULES (WATCHDOG) ENDPOINTS ---
from app.notifications.rule_repository import RuleRepository
from api.dependencies import get_rule_repository

@router.get("/rules")
def get_watchdog_rules(
    repo: RuleRepository = Depends(get_rule_repository)
) -> list[dict[str, Any]]:
    """Retorna regras ativas de monitoramento."""
    try:
        return repo._load_rules_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/rules/{rule_id}")
def delete_watchdog_rule(
    rule_id: str,
    repo: RuleRepository = Depends(get_rule_repository)
):
    """Remove uma regra de monitoramento."""
    try:
        repo.remove_rule(rule_id)
        return {"message": "Regra removida."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
def reset_account(
    config_service: UserConfigService = Depends(get_user_config_service)
):
    """
    ZONA DE PERIGO: Reseta a conta do usuário.
    """
    try:
        config_service.clear_config()
        return {"message": "Conta resetada com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
