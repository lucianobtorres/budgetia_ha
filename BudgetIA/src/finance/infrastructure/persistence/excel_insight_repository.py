from datetime import datetime, timedelta

import pandas as pd

import config
from config import ColunasInsights
from finance.domain.models.insight import Insight
from finance.domain.repositories.insight_repository import IInsightRepository
from finance.infrastructure.persistence.data_context import FinancialDataContext


class ExcelInsightRepository(IInsightRepository):
    """
    Implementação concreta do repositório de insights para Excel.
    """

    def __init__(self, context: FinancialDataContext):
        self._context = context
        self._sheet_name = config.NomesAbas.CONSULTORIA_IA

    def _to_entity(self, row: pd.Series) -> Insight:
        return Insight(
            id=int(row[ColunasInsights.ID])
            if pd.notna(row[ColunasInsights.ID])
            else None,
            date=pd.to_datetime(row[ColunasInsights.DATA]),
            type=str(row[ColunasInsights.TIPO]),
            title=str(row[ColunasInsights.TITULO]),
            details=str(row[ColunasInsights.DETALHES]),
            status=str(row[ColunasInsights.STATUS]),
        )

    def _to_row(self, i: Insight) -> dict:
        return {
            ColunasInsights.ID: i.id,
            ColunasInsights.DATA: i.date,
            ColunasInsights.TIPO: i.type,
            ColunasInsights.TITULO: i.title,
            ColunasInsights.DETALHES: i.details,
            ColunasInsights.STATUS: i.status,
        }

    def list_all(self, status: str | None = None) -> list[Insight]:
        df = self._context.get_dataframe(self._sheet_name)
        if df.empty:
            return []

        if status:
            df = df[df[ColunasInsights.STATUS] == status]

        return [self._to_entity(row) for _, row in df.iterrows()]

    def save(self, insight: Insight) -> Insight:
        df = self._context.get_dataframe(self._sheet_name)

        if insight.id is None:
            insight.id = int(df[ColunasInsights.ID].max() + 1) if not df.empty else 1
            new_row = pd.DataFrame([self._to_row(insight)])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            mask = df[ColunasInsights.ID] == insight.id
            if mask.any():
                idx = df.index[mask][0]
                row_data = self._to_row(insight)
                for col, val in row_data.items():
                    df.at[idx, col] = val
            else:
                new_row = pd.DataFrame([self._to_row(insight)])
                df = pd.concat([df, new_row], ignore_index=True)

        self._context.update_dataframe(self._sheet_name, df)
        return insight

    def update_status(self, insight_id: int, new_status: str) -> bool:
        df = self._context.get_dataframe(self._sheet_name)
        mask = df[ColunasInsights.ID] == insight_id
        if not mask.any():
            return False

        idx = df.index[mask][0]
        df.at[idx, ColunasInsights.STATUS] = new_status
        self._context.update_dataframe(self._sheet_name, df)
        return True

    def delete_old_insights(self, days: int) -> int:
        df = self._context.get_dataframe(self._sheet_name)
        if df.empty:
            return 0

        cutoff = datetime.now() - timedelta(days=days)
        mask = pd.to_datetime(df[ColunasInsights.DATA]) < cutoff

        count = mask.sum()
        df = df[~mask]
        self._context.update_dataframe(self._sheet_name, df)
        return int(count)
