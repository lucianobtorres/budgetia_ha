# Em: src/finance/strategies/default_strategy.py

from typing import Any

import pandas as pd

import config

from .base_strategy import BaseMappingStrategy


class DefaultStrategy(BaseMappingStrategy):
    """
    Estratégia para o layout padrão. Assume que as abas e colunas
    já correspondem ao layout do sistema (ou serão criadas).
    """

    def __init__(
        self, layout_config: dict[str, Any], mapeamento: dict[str, Any] | None = None
    ):
        super().__init__(layout_config, mapeamento)
        print("LOG: Estratégia 'DefaultStrategy' selecionada.")

    def map_transactions(self, df_bruto: pd.DataFrame) -> pd.DataFrame:
        """
        Para a estratégia padrão, apenas garantimos que as colunas
        do nosso layout de transações existam.
        """
        # Reutiliza a lógica genérica da classe base para garantir as colunas
        return self.map_other_sheet(df_bruto, config.NomesAbas.TRANSACOES)

    def unmap_transactions(self, df_interno: pd.DataFrame) -> pd.DataFrame:
        """
        Na estratégia padrão, o formato interno JÁ É o formato do usuário.
        Apenas retornamos o DataFrame como está.
        """
        # (Opcional: podemos remover colunas internas como 'ID Transacao' se quisermos)
        colunas_para_salvar = [
            col for col in df_interno.columns if col in self.colunas_transacoes
        ]

        # Retorna apenas as colunas definidas no layout, na ordem correta
        return df_interno[colunas_para_salvar]
