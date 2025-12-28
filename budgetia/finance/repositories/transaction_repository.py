# src/finance/repositories/transaction_repository.py
from typing import Any
import pandas as pd

import config
from config import ColunasTransacoes

# Imports relativos para "subir" um nível
from ..services.transaction_service import TransactionService
from .data_context import FinancialDataContext


class TransactionRepository:
    """
    Repositório para gerenciar TODA a lógica de
    acesso e manipulação de Transações.
    """

    def __init__(
        self, context: FinancialDataContext, transaction_service: TransactionService
    ) -> None:
        """
        Inicializa o repositório.

        Args:
            context: A Unidade de Trabalho (DataContext) que gerencia os DataFrames.
            calculator: O especialista em cálculos financeiros puros.
        """
        self._context = context
        self._transaction_service = transaction_service
        self._aba_nome = config.NomesAbas.TRANSACOES

    def get_all_transactions(self) -> pd.DataFrame:
        """Retorna o DataFrame completo de transações."""
        return self._context.get_dataframe(sheet_name=self._aba_nome)

    def add_transaction(
        self,
        data: str,
        tipo: str,
        categoria: str,
        descricao: str,
        valor: float,
        status: str = "Concluído",
    ) -> None:
        """
        Adiciona uma nova transação ao DataFrame em memória (no DataContext).
        """
        df = self.get_all_transactions()  # Pega a cópia atual

        novo_id = (
            (df[ColunasTransacoes.ID].max() + 1)
            if not df.empty
            and ColunasTransacoes.ID in df.columns
            and df[ColunasTransacoes.ID].notna().any()
            else 1
        )

        novo_registro = pd.DataFrame(
            [
                {
                    ColunasTransacoes.ID: novo_id,
                    ColunasTransacoes.DATA: pd.to_datetime(data),
                    ColunasTransacoes.TIPO: tipo,
                    ColunasTransacoes.CATEGORIA: categoria,
                    ColunasTransacoes.DESCRICAO: descricao,
                    ColunasTransacoes.VALOR: valor,
                    ColunasTransacoes.STATUS: status,
                }
            ],
            columns=config.LAYOUT_PLANILHA[self._aba_nome],
        )

        df_atualizado = pd.concat([df, novo_registro], ignore_index=True)

        self._context.update_dataframe(self._aba_nome, df_atualizado)
        print(f"LOG (Repo): Transação '{descricao}' adicionada ao contexto.")

    def delete_transaction(self, transaction_id: int) -> bool:
        """Exclui uma transação pelo ID."""
        df = self.get_all_transactions()
        if ColunasTransacoes.ID not in df.columns:
            return False
        
        # Ensure robust numeric comparison for ID
        ids = pd.to_numeric(df[ColunasTransacoes.ID], errors='coerce').fillna(-1).astype(int)
        
        if transaction_id not in ids.values:
             return False

        # Keep rows where ID is NOT the target
        df_novo = df[ids != transaction_id]
            
        self._context.update_dataframe(self._aba_nome, df_novo)
        return True

    def update_transaction(self, transaction_id: int, novos_dados: dict[str, Any]) -> bool:
        """Atualiza uma transação existente pelo ID."""
        df = self.get_all_transactions()
        if ColunasTransacoes.ID not in df.columns:
            return False
            
        # Robust ID matching
        ids = pd.to_numeric(df[ColunasTransacoes.ID], errors='coerce').fillna(-1).astype(int)
        mask = ids == transaction_id
        
        if not mask.any():
            return False
            
        # Atualiza os campos fornecidos
        # Mapeia chaves do dict (que vêm do Pydantic) para colunas do DataFrame
        # Ex: "descricao" -> "Descricao"
        
        # Mapeamento de chaves amigáveis (do input) para colunas reais
        field_map = {
            "data": ColunasTransacoes.DATA,
            "tipo": ColunasTransacoes.TIPO,
            "categoria": ColunasTransacoes.CATEGORIA,
            "descricao": ColunasTransacoes.DESCRICAO,
            "valor": ColunasTransacoes.VALOR,
            "status": ColunasTransacoes.STATUS
        }
        
        idx = df.index[mask][0]
        
        for field, valor in novos_dados.items():
            # Determina o nome real da coluna
            col_name = field
            if field in field_map:
                col_name = field_map[field]
            
            if col_name in df.columns and col_name != ColunasTransacoes.ID:
                if col_name == ColunasTransacoes.DATA:
                     df.at[idx, col_name] = pd.to_datetime(valor)
                elif col_name == ColunasTransacoes.VALOR:
                     # Garante float
                     try:
                        df.at[idx, col_name] = float(valor)
                     except:
                        df.at[idx, col_name] = valor
                else:
                     df.at[idx, col_name] = valor
                     
        self._context.update_dataframe(self._aba_nome, df)
        return True

    def get_summary(self) -> dict[str, float]:
        """Delega o cálculo do resumo para o FinancialCalculator."""
        df_transacoes = self.get_all_transactions()
        return self._transaction_service.get_summary(df_transacoes)

    def get_expenses_by_category(self, top_n: int = 5) -> pd.Series:
        """Delega o cálculo das despesas por categoria para o FinancialCalculator."""
        df_transacoes = self.get_all_transactions()
        return self._transaction_service.get_expenses_by_category(df_transacoes, top_n)
