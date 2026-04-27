from typing import Any

import pandas as pd
from fastapi import APIRouter, Body, Depends, HTTPException

from config import ColunasTransacoes, NomesAbas
from core.logger import get_logger
from finance.planilha_manager import PlanilhaManager
from interfaces.api.dependencies import get_planilha_manager
from interfaces.api.schemas.transactions import (
    TransactionCreate,
    TransactionSchema,
    TransactionUpdate,
)

logger = get_logger("TransactionsRouter")

router = APIRouter(prefix="/transactions", tags=["Transações"])


@router.get("/", response_model=list[TransactionSchema])
def listar_transacoes(
    limit: int = 100,
    month: int | None = None,
    year: int | None = None,
    manager: PlanilhaManager = Depends(get_planilha_manager),
):
    """
    Retorna a lista de transações da planilha.
    Suporta filtragem por mês e ano.
    """
    try:
        transactions = manager.list_transactions_use_case.execute(
            month=month, year=year, limit=limit
        )

        # Mapeia Entidade -> Schema
        # Nota: TransactionSchema espera strings para data e outros campos
        return [
            TransactionSchema(
                id=t.id,
                data=t.data.strftime("%Y-%m-%d"),
                tipo=t.tipo,
                categoria=t.categoria,
                descricao=t.descricao,
                valor=t.valor,
                status=t.status,
            )
            for t in transactions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict[str, Any])
def adicionar_transacao(
    transaction: TransactionCreate,
    manager: PlanilhaManager = Depends(get_planilha_manager),
):
    """
    Adiciona uma nova transação à planilha.
    Usa o Caso de Uso DDD.
    """
    from finance.domain.models.transaction import Transaction

    try:
        with manager.lock_file(timeout_seconds=60):
            manager.atualizar_dados()

            new_tx = Transaction(
                data=transaction.data,
                tipo=transaction.tipo,
                categoria=transaction.categoria,
                descricao=str(transaction.descricao),
                valor=transaction.valor,
                status=transaction.status,
            )

            manager.add_transaction_use_case.execute(new_tx)
            manager.salvar()
            return {"message": "Transação adicionada com sucesso."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar transação: {e}")


@router.put("/{transaction_id}")
def atualizar_transacao(
    transaction_id: int,
    transaction: TransactionUpdate,
    manager: PlanilhaManager = Depends(get_planilha_manager),
):
    from finance.domain.models.transaction import Transaction

    try:
        with manager.lock_file(timeout_seconds=60):
            manager.atualizar_dados()

            updated_tx = Transaction(
                id=transaction_id,
                data=transaction.data,
                tipo=transaction.tipo,
                categoria=transaction.categoria,
                descricao=str(transaction.descricao),
                valor=transaction.valor,
                status=transaction.status,
            )

            manager.update_transaction_use_case.execute(updated_tx)
            manager.salvar()

        return {"message": "Transação atualizada com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {e}")


@router.delete("/{transaction_id}")
def delete_item(
    transaction_id: int, manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    try:
        with manager.lock_file(timeout_seconds=60):
            manager.atualizar_dados()
            success = manager.delete_transaction_use_case.execute(transaction_id)
            if not success:
                raise HTTPException(status_code=404, detail="Transação não encontrada")
            manager.salvar()
        return {"message": "Transação removida."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bulk")
def update_transactions_bulk(
    transactions: list[dict[str, Any]] = Body(...),
    manager: PlanilhaManager = Depends(get_planilha_manager),
) -> dict[str, str]:
    """
    Atualiza TODAS as transações reescrevendo a aba.
    Espera uma lista de objetos que correspondem às colunas.
    """
    try:
        if not transactions:
            return {"message": "Nenhuma alteração enviada."}

        with manager.lock_file(timeout_seconds=120):  # Bulk pode demorar
            manager.atualizar_dados()
            # Converte lista de dicts de volta para DataFrame
            df_new = pd.DataFrame(transactions)

            # GARANTE que a coluna de Data seja datetime, pois o JSON envia string
            if ColunasTransacoes.DATA in df_new.columns:
                df_new[ColunasTransacoes.DATA] = pd.to_datetime(
                    df_new[ColunasTransacoes.DATA], errors="coerce"
                )

            # Atualiza via manager
            manager.update_dataframe(NomesAbas.TRANSACOES, df_new)
            manager.recalcular_orcamentos()
            manager.salvar()

        return {"message": f"{len(transactions)} transações atualizadas com sucesso."}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao atualizar transações: {e}"
        )


@router.post("/batch", response_model=dict[str, Any])
def adicionar_transacoes_em_lote(
    transactions: list[TransactionCreate],
    manager: PlanilhaManager = Depends(get_planilha_manager),
):
    """
    Adiciona múltiplas transações de uma vez.
    Eficiente para importações, pois salva apenas uma vez no final.
    """
    try:
        if not transactions:
            return {"message": "Nenhuma transação enviada."}

        with manager.lock_file(timeout_seconds=60):
            manager.atualizar_dados()

            # 1. Auto-Register New Categories
            existing_cols = manager.category_repo.get_all_category_names()
            # Normalize for comparison
            existing_norm = {c.lower() for c in existing_cols}

            new_categories_map = {}  # name -> type

            for tx in transactions:
                cat = tx.categoria
                if not cat or cat == "A Classificar" or cat == "Outros":
                    continue

                if cat.lower() not in existing_norm:
                    # New category found!
                    # Infer type based on transaction type (majority vote or first occurrence)
                    if cat not in new_categories_map:
                        new_categories_map[cat] = tx.tipo

            # Register them
            for cat_name, cat_type in new_categories_map.items():
                manager.category_repo.add_category(
                    nome=cat_name,
                    tipo=cat_type,  # Receita or Despesa
                    icone="HelpCircle",  # Generic icon
                    tags="Importado",
                )
                logger.info(
                    f"Categoria '{cat_name}' criada automaticamente via importação."
                )

            # 2. Add Transactions (Batch)
            # Converte objetos pydantic para dict
            tx_dicts = [
                {
                    "data": tx.data,
                    "tipo": tx.tipo,
                    "categoria": tx.categoria,
                    "descricao": str(tx.descricao),
                    "valor": tx.valor,
                    "status": tx.status,
                    "parcelas": tx.parcelas,
                }
                for tx in transactions
            ]

            count = manager.adicionar_registros_lote(tx_dicts)
            # Manager saves automatically inside batch method

        return {"message": f"{count} transações importadas com sucesso."}
    except Exception as e:
        logger.error(f"Erro no batch upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro na importação em lote: {e}")
