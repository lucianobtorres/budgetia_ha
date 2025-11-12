# src/finance/repositories/insight_repository.py

import pandas as pd

from config import LAYOUT_PLANILHA, ColunasInsights, NomesAbas

from .data_context import FinancialDataContext


class InsightRepository:
    """
    Repositório para gerenciar a lógica de acesso e manipulação
    dos dados de Insights da IA.
    """

    def __init__(self, context: FinancialDataContext) -> None:
        """
        Inicializa o repositório.

        Args:
            context: A Unidade de Trabalho (DataContext).
        """
        self._context = context
        self._aba_nome = NomesAbas.CONSULTORIA_IA

    def add_insight(
        self,
        data_insight: str,
        tipo_insight: str,
        titulo_insight: str,
        detalhes_recomendacao: str,
        status: str = "Novo",
    ) -> None:
        """Adiciona um insight gerado pela IA na aba 'Consultoria da IA'."""
        df_insight = self._context.get_dataframe(self._aba_nome)

        novo_id = (
            (df_insight[ColunasInsights.ID].max() + 1)
            if not df_insight.empty
            and ColunasInsights.ID in df_insight.columns
            and df_insight[ColunasInsights.ID].notna().any()
            else 1
        )

        novo_insight = pd.DataFrame(
            [
                {
                    ColunasInsights.ID: novo_id,
                    ColunasInsights.DATA: data_insight,
                    ColunasInsights.TIPO: tipo_insight,
                    ColunasInsights.TITULO: titulo_insight,
                    ColunasInsights.DETALHE: detalhes_recomendacao,
                    ColunasInsights.STATUS: status,
                }
            ],
            columns=LAYOUT_PLANILHA[self._aba_nome],
        )

        df_atualizado = pd.concat([df_insight, novo_insight], ignore_index=True)
        self._context.update_dataframe(self._aba_nome, df_atualizado)
        print(f"LOG (Repo): Insight de IA '{titulo_insight}' adicionado.")
