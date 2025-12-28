from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Body
from interfaces.api.dependencies import get_planilha_manager
from finance.planilha_manager import PlanilhaManager
from finance.schemas import AddTransactionInput
from config import NomesAbas, ColunasTransacoes

router = APIRouter(prefix="/transactions", tags=["Transações"])

@router.get("/")
def listar_transacoes(
    limit: int = 100,
    month: int | None = None,
    year: int | None = None,
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> list[dict[str, Any]]:
    """
    Retorna a lista de transações da planilha.
    Suporta filtragem por mês e ano.
    Se filtrado, retorna todas as transações do período (limitado a 1000 por segurança).
    Se não filtrado, retorna as 'limit' últimas.
    """
    try:
        # Pega o DataFrame da aba 'Transações'
        df = manager.visualizar_dados(NomesAbas.TRANSACOES)
        if df is None or df.empty:
            return []
        
        # Garante datetime para filtragem e ordenação
        if ColunasTransacoes.DATA in df.columns:
            # dayfirst=True assume DD/MM/YYYY
            df[ColunasTransacoes.DATA] = pd.to_datetime(df[ColunasTransacoes.DATA], dayfirst=True, errors='coerce')
        
        # Filtro de Mês/Ano
        if month is not None and year is not None:
            # Remove NaT antes de filtrar (ou apenas ignora)
            mask = (df[ColunasTransacoes.DATA].dt.month == month) & (df[ColunasTransacoes.DATA].dt.year == year)
            df = df.loc[mask]
            # Se filtrou por mês, queremos ver tudo (aumento o limit se não foi forçado alto)
            if limit == 100: # Se for o default
                limit = 1000

        # Converte NaT/NaN para None ou string para evitar erro de JSON
        # Para colunas de objeto, preenche "". Para data, volta pra string.
        df_display = df.copy()
        
        # Formata data para string ISO ou DD/MM/YYYY para o frontend? 
        # Frontend geralmente gosta de ISO. Mas o excel usa DD/MM/YYYY.
        # Vamos converter datetime para string YYYY-MM-DD para facilitar sort no JS
        if ColunasTransacoes.DATA in df_display.columns:
             df_display[ColunasTransacoes.DATA] = df_display[ColunasTransacoes.DATA].dt.strftime('%Y-%m-%d').replace('NaT', '')
            
        df_display = df_display.fillna("")

        # Garante que ID está presente e é int (se existir)
        if ColunasTransacoes.ID in df_display.columns:
             df_display[ColunasTransacoes.ID] = pd.to_numeric(df_display[ColunasTransacoes.ID], errors='coerce').fillna(0).astype(int)

        # Ordenação: Mais recente primeiro
        if ColunasTransacoes.DATA in df_display.columns:
             df_display = df_display.sort_values(by=ColunasTransacoes.DATA, ascending=False)

        # Converte para dict (records) para JSON
        registros: list[dict[str, Any]] = df_display.head(limit).to_dict(orient="records")
        return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{transaction_id}")
def atualizar_transacao(
    transaction_id: int,
    transaction: AddTransactionInput,
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, Any]:
    try:
        with manager.lock_file(timeout_seconds=60):
            manager.refresh_data()
            df = manager.visualizar_dados(NomesAbas.TRANSACOES)
            if df is None or df.empty:
                raise HTTPException(status_code=404, detail="Nenhuma transação encontrada.")
        
            # Ensure ID column is int for comparison
            if ColunasTransacoes.ID in df.columns:
                # We assume IDs are generally clean integers, but safety first
                df[ColunasTransacoes.ID] = pd.to_numeric(df[ColunasTransacoes.ID], errors='coerce').fillna(0).astype(int)
        
            # Find index
            mask = df[ColunasTransacoes.ID] == transaction_id
            if not mask.any():
                raise HTTPException(status_code=404, detail="Transação não encontrada.")
            
            idx = df.index[mask][0]
        
            # Update row
            # Convert date string to datetime if needed, or keep as is if manager handles it. 
            # PlanilhaManager usually expects datetime or compatible.
            df.at[idx, ColunasTransacoes.DATA] = pd.to_datetime(transaction.data)
            df.at[idx, ColunasTransacoes.TIPO] = transaction.tipo
            df.at[idx, ColunasTransacoes.CATEGORIA] = transaction.categoria
            df.at[idx, ColunasTransacoes.DESCRICAO] = str(transaction.descricao)
            df.at[idx, ColunasTransacoes.VALOR] = float(transaction.valor)
            df.at[idx, ColunasTransacoes.STATUS] = transaction.status
        
            manager.update_dataframe(NomesAbas.TRANSACOES, df)
            manager.recalculate_budgets() # Important to update budgets!
            manager.save()
        
        return {"message": "Transação atualizada com sucesso.", "data": transaction}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {e}")

@router.delete("/{transaction_id}")
def delete_item(
    transaction_id: int,
    manager: PlanilhaManager = Depends(get_planilha_manager)
) -> dict[str, str]:
    try:
        with manager.lock_file(timeout_seconds=60):
            manager.refresh_data()
            success = manager.delete_transaction(transaction_id)
            if not success:
                raise HTTPException(status_code=404, detail="Transação não encontrada")
            manager.save()
        return {"message": "Transação removida."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            
        with manager.lock_file(timeout_seconds=120): # Bulk pode demorar
            manager.refresh_data()
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
        with manager.lock_file(timeout_seconds=60):
            # Atomic: Refresh -> Add -> Save
            manager.refresh_data()
            manager.adicionar_registro(
                data=transaction.data,
                tipo=transaction.tipo,
                categoria=transaction.categoria,
                descricao=str(transaction.descricao),
                valor=transaction.valor,
                status=transaction.status
            )
            # Save is automatic inside adicionar_registro? NO.
            # Manager.adicionar_registro calls repo.add which updates DF. 
            # It DOES NOT call save().
            # Wait, looking at the ORIGINAL code below:
            # manager.adicionar_registro(...)
            # return ...
            # THERE WAS NO manager.save() call in the original code? 
            # Let me check the original file again.
            
            manager.save() # Ensure save is called
            
        return {"message": "Transação adicionada com sucesso", "data": transaction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar transação: {e}")
