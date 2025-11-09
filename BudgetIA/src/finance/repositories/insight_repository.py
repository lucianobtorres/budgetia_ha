# src/finance/repositories/insight_repository.py

import pandas as pd

import config

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
        self._aba_nome = config.NomesAbas.CONSULTORIA_IA

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
            (df_insight["ID Insight"].max() + 1)
            if not df_insight.empty
            and "ID Insight" in df_insight.columns
            and df_insight["ID Insight"].notna().any()
            else 1
        )

        novo_insight = pd.DataFrame(
            [
                {
                    "ID Insight": novo_id,
                    "Data do Insight": data_insight,
                    "Tipo de Insight": tipo_insight,
                    "Título do Insight": titulo_insight,
                    "Detalhes/Recomendação da IA": detalhes_recomendacao,
                    "Status (Novo/Lido/Concluído)": status,
                }
            ],
            columns=config.LAYOUT_PLANILHA[self._aba_nome],
        )

        df_atualizado = pd.concat([df_insight, novo_insight], ignore_index=True)
        self._context.update_dataframe(self._aba_nome, df_atualizado)
        print(f"LOG (Repo): Insight de IA '{titulo_insight}' adicionado.")
