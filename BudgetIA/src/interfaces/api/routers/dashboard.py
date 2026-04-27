from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from finance.planilha_manager import PlanilhaManager
from interfaces.api.dependencies import get_planilha_manager

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_summary(
    manager: PlanilhaManager = Depends(get_planilha_manager),
) -> dict[str, float]:
    """Retorna saldo, receitas e despesas."""
    from config import SummaryKeys

    try:
        res = manager.get_summary_use_case.execute()
        # Mapeia para as chaves esperadas pelo front
        return {
            SummaryKeys.RECEITAS: res["total_receitas"],
            SummaryKeys.DESPESAS: res["total_despesas"],
            SummaryKeys.SALDO: res["saldo"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expenses_by_category")
def get_expenses_chart(
    top_n: int = 5, manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, float]:
    """Retorna dados para o gráfico de despesas."""
    try:
        return manager.get_expenses_by_category_use_case.execute(top_n=top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budgets")
def get_budgets_status(
    manager: PlanilhaManager = Depends(get_planilha_manager),
) -> list[dict[str, Any]]:
    """Retorna status dos orçamentos mensais ativos."""
    try:
        budgets = manager.list_budgets_use_case.execute()
        # Filtra ativos e mensais e converte para dict
        return [b.model_dump() for b in budgets if b.periodo == "Mensal"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
def export_excel(manager: PlanilhaManager = Depends(get_planilha_manager)) -> Response:
    """Retorna o arquivo Excel atual como download."""
    try:
        # Reusa a lógica de exportação (BytesIO)
        # Nota: O ideal seria ter o método no manager, mas está em `web_app.utils`.
        # Vamos ler o arquivo do disco diretamente via manager.storage.

        file_path = manager._context.storage.file_path

        with open(file_path, "rb") as f:
            file_content = f.read()

        return Response(
            content=file_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=budget_export.xlsx"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar: {e}")
