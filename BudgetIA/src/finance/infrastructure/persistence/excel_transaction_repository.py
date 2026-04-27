import pandas as pd

import config
from config import ColunasTransacoes
from finance.domain.models.transaction import Transaction
from finance.domain.repositories.transaction_repository import ITransactionRepository
from finance.infrastructure.persistence.data_context import FinancialDataContext


class ExcelTransactionRepository(ITransactionRepository):
    """
    Implementação concreta do repositório de transações usando Excel/DataFrames como persistência.
    Faz a ponte entre as Entidades de Domínio e o FinancialDataContext.
    """

    def __init__(self, context: FinancialDataContext):
        self._context = context
        self._sheet_name = config.NomesAbas.TRANSACOES

    def _to_entity(self, row: pd.Series) -> Transaction:
        """Converte uma linha do DataFrame para uma Entidade Transaction."""
        return Transaction(
            id=int(row[ColunasTransacoes.ID])
            if pd.notna(row[ColunasTransacoes.ID])
            else None,
            data=pd.to_datetime(row[ColunasTransacoes.DATA]).date(),
            tipo=str(row[ColunasTransacoes.TIPO]),
            categoria=str(row[ColunasTransacoes.CATEGORIA]),
            descricao=str(row[ColunasTransacoes.DESCRICAO]),
            valor=float(row[ColunasTransacoes.VALOR]),
            status=str(row[ColunasTransacoes.STATUS])
            if pd.notna(row[ColunasTransacoes.STATUS])
            else "Concluído",
        )

    def _to_row(self, tx: Transaction) -> dict:
        """Converte uma Entidade Transaction para um dicionário de linha do DataFrame."""
        return {
            ColunasTransacoes.ID: tx.id,
            ColunasTransacoes.DATA: pd.to_datetime(tx.data),
            ColunasTransacoes.TIPO: tx.tipo,
            ColunasTransacoes.CATEGORIA: tx.categoria,
            ColunasTransacoes.DESCRICAO: tx.descricao,
            ColunasTransacoes.VALOR: tx.valor,
            ColunasTransacoes.STATUS: tx.status,
        }

    def save(self, transaction: Transaction) -> Transaction:
        """Salva ou atualiza uma transação no DataFrame em memória."""
        df = self._context.get_dataframe(self._sheet_name)

        if transaction.id is None:
            # Geração de ID Incremental
            next_id = 1
            if not df.empty and ColunasTransacoes.ID in df.columns:
                next_id = (
                    pd.to_numeric(df[ColunasTransacoes.ID], errors="coerce")
                    .fillna(0)
                    .max()
                    + 1
                )
            transaction.id = int(next_id)

            # Adiciona nova linha
            new_row_dict = self._to_row(transaction)
            # Garantir que todas as colunas do layout estejam presentes para evitar erros de concat
            new_row = pd.DataFrame([new_row_dict])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            # Atualização de registro existente
            mask = df[ColunasTransacoes.ID] == transaction.id
            idx = df.index[mask]

            if not idx.empty:
                row_data = self._to_row(transaction)
                for col, val in row_data.items():
                    if col in df.columns:
                        if isinstance(val, str) and pd.api.types.is_numeric_dtype(
                            df[col]
                        ):
                            df[col] = df[col].astype(object)
                        df.at[idx[0], col] = val
            else:
                raise ValueError(
                    f"Transação com ID {transaction.id} não encontrada para atualização."
                )

        self._context.update_dataframe(self._sheet_name, df)
        return transaction

    def save_batch(self, transactions: list[Transaction]) -> int:
        """Otimiza a gravação de múltiplas transações."""
        # Para simplificar nesta fase inicial, usamos o save individual
        # mas mantendo a interface correta.
        for tx in transactions:
            self.save(tx)
        return len(transactions)

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Busca uma transação específica."""
        df = self._context.get_dataframe(self._sheet_name)
        if df.empty:
            return None

        row = df[df[ColunasTransacoes.ID] == transaction_id]
        if row.empty:
            return None
        return self._to_entity(row.iloc[0])

    def delete(self, transaction_id: int) -> bool:
        """Remove uma transação do DataFrame."""
        df = self._context.get_dataframe(self._sheet_name)
        mask = df[ColunasTransacoes.ID] == transaction_id
        if not mask.any():
            return False

        df = df[~mask]
        self._context.update_dataframe(self._sheet_name, df)
        return True

    def list_all(
        self, month: int | None = None, year: int | None = None
    ) -> list[Transaction]:
        """Lista transações convertidas em entidades com filtros opcionais."""
        df = self._context.get_dataframe(self._sheet_name)
        if df.empty:
            return []

        # Filtros de tempo usando as capacidades do pandas
        temp_df = df.copy()
        temp_df[ColunasTransacoes.DATA] = pd.to_datetime(
            temp_df[ColunasTransacoes.DATA]
        )

        if year:
            temp_df = temp_df[temp_df[ColunasTransacoes.DATA].dt.year == year]
        if month:
            temp_df = temp_df[temp_df[ColunasTransacoes.DATA].dt.month == month]

        return [self._to_entity(row) for _, row in temp_df.iterrows()]
