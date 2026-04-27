from fastapi import APIRouter, Depends, HTTPException

from finance.planilha_manager import PlanilhaManager
from interfaces.api.dependencies import get_planilha_manager
from interfaces.api.schemas.debts import DebtCreate, DebtSchema

router = APIRouter(prefix="/debts", tags=["Dívidas"])


@router.get("/", response_model=list[DebtSchema])
def list_debts(manager: PlanilhaManager = Depends(get_planilha_manager)):
    """Lista todas as dívidas."""
    try:
        debts = manager.list_debts_use_case.execute()
        # O Pydantic resolve o mapeamento se os nomes forem iguais ou via Config
        return debts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=bool)
def create_debt(
    debt: DebtCreate, manager: PlanilhaManager = Depends(get_planilha_manager)
):
    """Cria uma nova dívida."""
    from datetime import datetime

    from finance.domain.models.debt import Debt

    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()

            # Converte Schema -> Entidade
            data_pgto = (
                datetime.combine(debt.data_proximo_pgto, datetime.min.time())
                if debt.data_proximo_pgto
                else None
            )

            new_debt = Debt(
                nome=debt.nome,
                valor_original=debt.valor_original,
                taxa_juros_mensal=debt.taxa_juros_mensal,
                parcelas_totais=debt.parcelas_totais,
                parcelas_pagas=debt.parcelas_pagas,
                valor_parcela=debt.valor_parcela,
                data_proximo_pgto=data_pgto,
                observacoes=debt.observacoes or "",
            )

            manager.add_or_update_debt_use_case.execute(new_debt)
            manager.save()
            return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{debt_id}", response_model=bool)
def update_debt(
    debt_id: int,
    debt: DebtCreate,
    manager: PlanilhaManager = Depends(get_planilha_manager),
):
    """Atualiza uma dívida existente."""
    from datetime import datetime

    from finance.domain.models.debt import Debt

    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()

            data_pgto = (
                datetime.combine(debt.data_proximo_pgto, datetime.min.time())
                if debt.data_proximo_pgto
                else None
            )

            updated_debt = Debt(
                id=debt_id,
                nome=debt.nome,
                valor_original=debt.valor_original,
                taxa_juros_mensal=debt.taxa_juros_mensal,
                parcelas_totais=debt.parcelas_totais,
                parcelas_pagas=debt.parcelas_pagas,
                valor_parcela=debt.valor_parcela,
                data_proximo_pgto=data_pgto,
                observacoes=debt.observacoes or "",
            )

            manager.add_or_update_debt_use_case.execute(updated_debt)
            manager.save()
            return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{debt_id}", response_model=bool)
def delete_debt(debt_id: int, manager: PlanilhaManager = Depends(get_planilha_manager)):
    """Remove uma dívida."""
    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()
            success = manager.delete_debt_use_case.execute(debt_id)
            if success:
                manager.salvar()
            return success
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
