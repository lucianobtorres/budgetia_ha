import traceback

from fastapi import APIRouter, Depends, HTTPException

from core.logger import get_logger
from finance.planilha_manager import PlanilhaManager
from interfaces.api.dependencies import get_planilha_manager
from interfaces.api.schemas.budgets import BudgetCreate, BudgetSchema

logger = get_logger("BudgetsRouter")

router = APIRouter(prefix="/budgets", tags=["Orçamentos"])


@router.get("/", response_model=list[BudgetSchema])
def listar_orcamentos(manager: PlanilhaManager = Depends(get_planilha_manager)):
    """
    Retorna a lista completa de orçamentos para edição.
    """
    try:
        budgets = manager.list_budgets_use_case.execute()

        # Mapeia de Domain Budget para BudgetSchema da API
        # O Pydantic resolve os aliases se passarmos os nomes das propriedades da entidade
        return [
            BudgetSchema(
                id=b.id,
                categoria=b.categoria,
                valor_limite=b.limite,
                valor_gasto_atual=b.gasto_atual,
                porcentagem_gasta=b.percentual_gasto,
                periodo=b.periodo,
                status=b.status,
                observacoes=b.observacoes,
            )
            for b in budgets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict[str, str])
def add_orcamento(
    budget: BudgetCreate, manager: PlanilhaManager = Depends(get_planilha_manager)
):
    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()
            # Usa o método correto do manager
            msg = manager.adicionar_ou_atualizar_orcamento(
                budget.categoria,
                budget.valor_limite,
                budget.periodo,
                budget.observacoes,
            )
            manager.save()
        return {"message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{budget_id}", response_model=dict[str, str])
def update_orcamento_item(
    budget_id: int,
    budget: BudgetCreate,
    manager: PlanilhaManager = Depends(get_planilha_manager),
):
    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()
            # Usa nomes de campo Pydantic (não colunas Excel) para compatibilidade
            # com UpdateBudgetUseCase que faz model_dump() + update() + Budget(**data)
            dados = {
                "categoria": budget.categoria,
                "limite": budget.valor_limite,
                "periodo": budget.periodo,
                "observacoes": budget.observacoes,
            }
            success = manager.atualizar_orcamento(budget_id, dados)
            if not success:
                raise HTTPException(status_code=404, detail="Orçamento não encontrado")
            manager.save()
        return {"message": "Orçamento atualizado."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao atualizar orçamento {budget_id}:\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{budget_id}")
def delete_orcamento_item(
    budget_id: int, manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()
            success = manager.excluir_orcamento(budget_id)
            if not success:
                raise HTTPException(status_code=404, detail="Orçamento não encontrado")
            manager.save()
        return {"message": "Orçamento removido."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
