from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Body
from api.dependencies import get_planilha_manager
from finance.planilha_manager import PlanilhaManager
from config import NomesAbas

router = APIRouter(prefix="/budgets", tags=["Orçamentos"])

@router.get("/")
def listar_orcamentos(
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> list[dict[str, Any]]:
    """
    Retorna a lista completa de orçamentos para edição.
    """
    try:
        df = manager.visualizar_dados(NomesAbas.ORCAMENTOS)
        if df is None or df.empty:
            return []
        return df.to_dict(orient="records") # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/bulk")
def update_orcamentos_bulk(
    budgets: list[dict[str, Any]] = Body(...),
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    """
    Atualiza TODOS os orçamentos reescrevendo a aba.
    """
    try:
        if not budgets:
            return {"message": "Nenhuma alteração enviada."}
            
        df_new = pd.DataFrame(budgets)
        
        manager.update_dataframe(NomesAbas.ORCAMENTOS, df_new)
        manager.recalculate_budgets()
        manager.save()
        
        return {"message": f"{len(budgets)} orçamentos atualizados com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar orçamentos: {e}")
