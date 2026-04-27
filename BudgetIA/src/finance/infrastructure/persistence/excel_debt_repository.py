import pandas as pd

import config
from config import ColunasDividas
from finance.domain.models.debt import Debt
from finance.domain.repositories.debt_repository import IDebtRepository
from finance.infrastructure.persistence.data_context import FinancialDataContext


class ExcelDebtRepository(IDebtRepository):
    """
    Implementação concreta do repositório de dívidas para Excel.
    """

    def __init__(self, context: FinancialDataContext):
        self._context = context
        self._sheet_name = config.NomesAbas.DIVIDAS

    def _to_entity(self, row: pd.Series) -> Debt:
        return Debt(
            id=int(row[ColunasDividas.ID])
            if pd.notna(row[ColunasDividas.ID])
            else None,
            nome=str(row[ColunasDividas.NOME]),
            valor_original=float(row[ColunasDividas.VALOR_ORIGINAL]),
            saldo_devedor_atual=float(row[ColunasDividas.SALDO_DEVEDOR]),
            taxa_juros_mensal=float(row[ColunasDividas.TAXA_JUROS]),
            parcelas_totais=int(row[ColunasDividas.PARCELAS_TOTAIS]),
            parcelas_pagas=int(row[ColunasDividas.PARCELAS_PAGAS]),
            valor_parcela=float(row[ColunasDividas.VALOR_PARCELA]),
            data_proximo_pgto=pd.to_datetime(row[ColunasDividas.DATA_PGTO])
            if pd.notna(row[ColunasDividas.DATA_PGTO])
            else None,
            data_inicio=pd.to_datetime(row[ColunasDividas.DATA_INICIO])
            if pd.notna(row[ColunasDividas.DATA_INICIO])
            else None,
            observacoes=str(row[ColunasDividas.OBS])
            if pd.notna(row[ColunasDividas.OBS])
            else "",
        )

    def _to_row(self, d: Debt) -> dict:
        return {
            ColunasDividas.ID: d.id,
            ColunasDividas.NOME: d.nome,
            ColunasDividas.VALOR_ORIGINAL: d.valor_original,
            ColunasDividas.SALDO_DEVEDOR: d.saldo_devedor_atual,
            ColunasDividas.TAXA_JUROS: d.taxa_juros_mensal,
            ColunasDividas.PARCELAS_TOTAIS: d.parcelas_totais,
            ColunasDividas.PARCELAS_PAGAS: d.parcelas_pagas,
            ColunasDividas.VALOR_PARCELA: d.valor_parcela,
            ColunasDividas.DATA_PGTO: d.data_proximo_pgto,
            ColunasDividas.DATA_INICIO: d.data_inicio,
            ColunasDividas.OBS: d.observacoes,
        }

    def list_all(self) -> list[Debt]:
        df = self._context.get_dataframe(self._sheet_name)
        if df.empty:
            return []
        return [self._to_entity(row) for _, row in df.iterrows()]

    def get_by_id(self, debt_id: int) -> Debt | None:
        df = self._context.get_dataframe(self._sheet_name)
        row = df[df[ColunasDividas.ID] == debt_id]
        if row.empty:
            return None
        return self._to_entity(row.iloc[0])

    def get_by_name(self, name: str) -> Debt | None:
        df = self._context.get_dataframe(self._sheet_name)
        mask = df[ColunasDividas.NOME].astype(str).str.lower() == name.lower()
        row = df[mask]
        if row.empty:
            return None
        return self._to_entity(row.iloc[0])

    def save(self, debt: Debt) -> Debt:
        df = self._context.get_dataframe(self._sheet_name)

        if debt.id is None:
            debt.id = int(df[ColunasDividas.ID].max() + 1) if not df.empty else 1
            new_row = pd.DataFrame([self._to_row(debt)])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            mask = df[ColunasDividas.ID] == debt.id
            if mask.any():
                idx = df.index[mask][0]
                row_data = self._to_row(debt)
                for col, val in row_data.items():
                    df.at[idx, col] = val
            else:
                new_row = pd.DataFrame([self._to_row(debt)])
                df = pd.concat([df, new_row], ignore_index=True)

        self._context.update_dataframe(self._sheet_name, df)
        return debt

    def delete(self, debt_id: int) -> bool:
        df = self._context.get_dataframe(self._sheet_name)
        mask = df[ColunasDividas.ID] == debt_id
        if not mask.any():
            return False
        df = df[~mask]
        self._context.update_dataframe(self._sheet_name, df)
        return True
