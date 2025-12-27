from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Body
from interfaces.api.dependencies import get_planilha_manager
from finance.planilha_manager import PlanilhaManager
from config import NomesAbas, ColunasOrcamentos

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
        
        if ColunasOrcamentos.ID in df.columns:
             df = df.copy() # Evita SettingWithCopy warning
             df[ColunasOrcamentos.ID] = pd.to_numeric(df[ColunasOrcamentos.ID], errors='coerce').fillna(0).astype(int)

        return df.to_dict(orient="records") # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
def add_orcamento(
    categoria: str = Body(...),
    valor_limite: float = Body(...),
    periodo: str = Body("Mensal"),
    observacoes: str = Body(""),
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()
            # Usa o método correto do manager
            msg = manager.adicionar_ou_atualizar_orcamento(categoria, valor_limite, periodo, observacoes)
            manager.save()
        return {"message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{budget_id}")
def update_orcamento_item(
    budget_id: int,
    categoria: str = Body(...),
    valor_limite: float = Body(...),
    periodo: str = Body("Mensal"),
    observacoes: str = Body(""),
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()
            dados = {
                ColunasOrcamentos.CATEGORIA: categoria,
                ColunasOrcamentos.LIMITE: valor_limite,
                ColunasOrcamentos.PERIODO: periodo,
                ColunasOrcamentos.OBS: observacoes
            }
            success = manager.update_budget(budget_id, dados)
            if not success:
                 raise HTTPException(status_code=404, detail="Orçamento não encontrado")
            manager.save()
        return {"message": "Orçamento atualizado."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{budget_id}")
def delete_orcamento_item(
    budget_id: int,
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()
            success = manager.delete_budget(budget_id)
            if not success:
                raise HTTPException(status_code=404, detail="Orçamento não encontrado")
            manager.save()
        return {"message": "Orçamento removido."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
