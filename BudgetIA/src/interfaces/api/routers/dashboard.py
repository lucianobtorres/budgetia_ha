from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from interfaces.api.dependencies import get_planilha_manager
from finance.planilha_manager import PlanilhaManager
from config import SummaryKeys, NomesAbas, ColunasOrcamentos

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_summary(
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, float]:
    """Retorna saldo, receitas e despesas."""
    try:
        return manager.get_summary() # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/expenses_by_category")
def get_expenses_chart(
    top_n: int = 5,
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, float]:
    """Retorna dados para o gráfico de despesas."""
    try:
        df = manager.get_expenses_by_category(top_n=top_n)
        # Converter Series para Dict
        return df.to_dict() # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/budgets")
def get_budgets_status(
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> list[dict[str, Any]]:
    """Retorna status dos orçamentos mensais ativos."""
    try:
        df = manager.visualizar_dados(aba_nome=NomesAbas.ORCAMENTOS)
        if df is None or df.empty:
            return []
            
        # Filtra ativos e mensais
        orcamentos_ativos = df[
            (df[ColunasOrcamentos.PERIODO] == "Mensal")
        ]
        
        return orcamentos_ativos.to_dict(orient="records") # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
def export_excel(
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> Response:
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
            headers={"Content-Disposition": "attachment; filename=budget_export.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar: {e}")
