from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Body
from api.dependencies import get_planilha_manager
from finance.planilha_manager import PlanilhaManager
from finance.schemas import AddTransactionInput
from config import NomesAbas, ColunasTransacoes

router = APIRouter(prefix="/transactions", tags=["Transações"])

@router.get("/")
def listar_transacoes(
    limit: int = 50,
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> list[dict[str, Any]]:
    """
    Retorna a lista de transações da planilha.
    Por padrão retorna as 50 mais recentes (ou o que o DataFrame retornar).
    """
    try:
        # Pega o DataFrame da aba 'Transações'
        df = manager.visualizar_dados(NomesAbas.TRANSACOES)
        if df is None or df.empty:
            return []
        
        # Converte NaT/NaN para None ou string para evitar erro de JSON
        df = df.fillna("")
        # Se houver colunas de data que viraram NaT, converte para string
        for col in df.select_dtypes(include=['datetime', 'datetimetz']).columns:
            df[col] = df[col].astype(str).replace('NaT', '')
            
        # Converte para dict (records) para JSON
        # tail(limit) pega as últimas (assumindo ordem cronológica de inserção)
        registros: list[dict[str, Any]] = df.tail(limit).to_dict(orient="records")
        return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
def adicionar_transacao(
    transaction: AddTransactionInput,
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, Any]:
    """
    Adiciona uma nova transação à planilha.
    Usa o mesmo Schema que a IA usa.
    """
    try:
        manager.adicionar_registro(
            data=transaction.data,  # type: ignore
            tipo=transaction.tipo,
            categoria=transaction.categoria,
            descricao=str(transaction.descricao),
            valor=transaction.valor,
            status=transaction.status
        )
        return {"message": "Transação adicionada com sucesso", "data": transaction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar transação: {e}")

@router.put("/bulk")
def update_transactions_bulk(
    transactions: list[dict[str, Any]] = Body(...),
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    """
    Atualiza TODAS as transações reescrevendo a aba.
    Espera uma lista de objetos que correspondem às colunas.
    """
    try:
        if not transactions:
            return {"message": "Nenhuma alteração enviada."}
            
        # Converte lista de dicts de volta para DataFrame
        df_new = pd.DataFrame(transactions)
        
        # GARANTE que a coluna de Data seja datetime, pois o JSON envia string
        if ColunasTransacoes.DATA in df_new.columns:
            df_new[ColunasTransacoes.DATA] = pd.to_datetime(
                df_new[ColunasTransacoes.DATA], errors='coerce'
            )

        # Atualiza via manager
        manager.update_dataframe(NomesAbas.TRANSACOES, df_new)
        manager.recalculate_budgets()
        manager.save()
        
        return {"message": f"{len(transactions)} transações atualizadas com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar transações: {e}")
