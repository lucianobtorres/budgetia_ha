import pandas as pd

import config
from config import ColunasOrcamentos
from finance.domain.models.budget import Budget
from finance.domain.repositories.budget_repository import IBudgetRepository
from finance.infrastructure.persistence.data_context import FinancialDataContext


class ExcelBudgetRepository(IBudgetRepository):
    """
    Implementação concreta do repositório de orçamentos para Excel.
    """

    def __init__(self, context: FinancialDataContext):
        self._context = context
        self._sheet_name = config.NomesAbas.ORCAMENTOS

    def _to_entity(self, row: pd.Series) -> Budget:
        """Converte linha do DataFrame para Entidade Budget."""
        return Budget(
            id=int(row[ColunasOrcamentos.ID])
            if pd.notna(row[ColunasOrcamentos.ID])
            else None,
            categoria=str(row[ColunasOrcamentos.CATEGORIA]),
            limite=float(row[ColunasOrcamentos.LIMITE]),
            gasto_atual=float(row[ColunasOrcamentos.GASTO])
            if pd.notna(row[ColunasOrcamentos.GASTO])
            else 0.0,
            periodo=str(row[ColunasOrcamentos.PERIODO])
            if pd.notna(row[ColunasOrcamentos.PERIODO])
            else "Mensal",
            observacoes=str(row[ColunasOrcamentos.OBS])
            if pd.notna(row[ColunasOrcamentos.OBS])
            else None,
        )

    def _to_row(self, b: Budget) -> dict:
        """Converte Entidade Budget para dicionário de linha do DataFrame."""
        return {
            ColunasOrcamentos.ID: b.id,
            ColunasOrcamentos.CATEGORIA: b.categoria,
            ColunasOrcamentos.LIMITE: b.limite,
            ColunasOrcamentos.GASTO: b.gasto_atual,
            ColunasOrcamentos.PERCENTUAL: b.percentual_gasto,
            ColunasOrcamentos.PERIODO: b.periodo,
            ColunasOrcamentos.STATUS: b.status,
            ColunasOrcamentos.OBS: b.observacoes,
            ColunasOrcamentos.ATUALIZACAO: pd.Timestamp.now(),
        }

    def save(self, budget: Budget) -> Budget:
        """Salva ou atualiza um orçamento no DataFrame."""
        df = self._context.get_dataframe(self._sheet_name)

        if budget.id is None:
            # Geração de ID Incremental
            next_id = 1
            if not df.empty and ColunasOrcamentos.ID in df.columns:
                next_id = (
                    pd.to_numeric(df[ColunasOrcamentos.ID], errors="coerce")
                    .fillna(0)
                    .max()
                    + 1
                )
            budget.id = int(next_id)

            new_row = pd.DataFrame([self._to_row(budget)])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            # Atualização por ID — substitui a linha inteira para evitar conflito de dtype
            mask = df[ColunasOrcamentos.ID] == budget.id
            idx = df.index[mask]
            if not idx.empty:
                row_data = self._to_row(budget)
                # Substitui a linha inteira via loc; converte colunas de string
                # explicitamente para evitar FutureWarning do pandas
                for col, val in row_data.items():
                    if col in df.columns:
                        # Converte a coluna para object se o valor for string e a coluna for numérica
                        if isinstance(val, str) and pd.api.types.is_numeric_dtype(
                            df[col]
                        ):
                            df[col] = df[col].astype(object)
                        df.at[idx[0], col] = val
            else:
                raise ValueError(f"Orçamento ID {budget.id} não encontrado.")

        self._context.update_dataframe(self._sheet_name, df)
        return budget

    def get_by_id(self, budget_id: int) -> Budget | None:
        df = self._context.get_dataframe(self._sheet_name)
        row = df[df[ColunasOrcamentos.ID] == budget_id]
        if row.empty:
            return None
        return self._to_entity(row.iloc[0])

    def get_by_category(self, category: str) -> Budget | None:
        df = self._context.get_dataframe(self._sheet_name)
        row = df[df[ColunasOrcamentos.CATEGORIA] == category]
        if row.empty:
            return None
        return self._to_entity(row.iloc[0])

    def list_all(self) -> list[Budget]:
        df = self._context.get_dataframe(self._sheet_name)
        return [self._to_entity(row) for _, row in df.iterrows()]

    def delete(self, budget_id: int) -> bool:
        df = self._context.get_dataframe(self._sheet_name)
        mask = df[ColunasOrcamentos.ID] == budget_id
        if not mask.any():
            return False
        df = df[~mask]
        self._context.update_dataframe(self._sheet_name, df)
        return True
