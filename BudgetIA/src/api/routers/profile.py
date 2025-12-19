from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Body
from api.dependencies import get_planilha_manager
from finance.planilha_manager import PlanilhaManager
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
