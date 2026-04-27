import pandas as pd

import config
from config import ColunasMetas

from ...domain.models.goal import Goal
from ...domain.repositories.goal_repository import IGoalRepository
from .data_context import FinancialDataContext


class ExcelGoalRepository(IGoalRepository):
    """
    Implementação do repositório de metas usando Excel/Pandas como persistência.
    """

    def __init__(self, context: FinancialDataContext):
        self._context = context
        self._aba_nome = config.NomesAbas.METAS

    def _to_entity(self, row: pd.Series) -> Goal:
        """Converte uma linha do DataFrame para a Entidade Goal."""
        return Goal(
            id=int(row[ColunasMetas.ID]) if pd.notna(row[ColunasMetas.ID]) else None,
            nome=str(row[ColunasMetas.NOME]),
            valor_alvo=float(row[ColunasMetas.VALOR_ALVO]),
            valor_atual=float(row[ColunasMetas.VALOR_ATUAL]),
            data_alvo=pd.to_datetime(row[ColunasMetas.DATA_ALVO]).date()
            if pd.notna(row[ColunasMetas.DATA_ALVO])
            else None,
            status=str(row[ColunasMetas.STATUS]),
            observacoes=str(row[ColunasMetas.OBS])
            if pd.notna(row[ColunasMetas.OBS])
            else "",
        )

    def _to_row(self, goal: Goal) -> dict:
        """Converte a Entidade Goal para um dicionário compatível com DataFrame."""
        return {
            ColunasMetas.ID: goal.id,
            ColunasMetas.NOME: goal.nome,
            ColunasMetas.VALOR_ALVO: goal.valor_alvo,
            ColunasMetas.VALOR_ATUAL: goal.valor_atual,
            ColunasMetas.DATA_ALVO: pd.to_datetime(goal.data_alvo)
            if goal.data_alvo
            else None,
            ColunasMetas.STATUS: goal.status,
            ColunasMetas.OBS: goal.observacoes,
        }

    def save(self, goal: Goal) -> Goal:
        """Salva ou atualiza uma meta na planilha."""
        df = self._context.get_dataframe(self._aba_nome)

        # Se ID for None, gera um novo
        if goal.id is None:
            goal.id = int(df[ColunasMetas.ID].max() + 1) if not df.empty else 1
            new_row = pd.DataFrame([self._to_row(goal)])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            # Atualiza linha existente
            mask = df[ColunasMetas.ID] == goal.id
            if mask.any():
                idx = df[mask].index[0]
                for k, v in self._to_row(goal).items():
                    df.at[idx, k] = v
            else:
                # Se não encontrar (ex: ID informado manualmente que não existe)
                new_row = pd.DataFrame([self._to_row(goal)])
                df = pd.concat([df, new_row], ignore_index=True)

        self._context.update_dataframe(self._aba_nome, df)
        return goal

    def get_by_id(self, goal_id: int) -> Goal | None:
        df = self._context.get_dataframe(self._aba_nome)
        mask = df[ColunasMetas.ID] == goal_id
        if not mask.any():
            return None
        return self._to_entity(df[mask].iloc[0])

    def list_all(self) -> list[Goal]:
        df = self._context.get_dataframe(self._aba_nome)
        return [self._to_entity(row) for _, row in df.iterrows()]

    def delete(self, goal_id: int) -> bool:
        df = self._context.get_dataframe(self._aba_nome)
        mask = df[ColunasMetas.ID] == goal_id
        if not mask.any():
            return False

        df = df[~mask]
        self._context.update_dataframe(self._aba_nome, df)
        return True
