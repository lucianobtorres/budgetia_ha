from typing import Any

import pandas as pd

import config
from finance.strategies.base_strategy import BaseMappingStrategy


class CustomStrategy(BaseMappingStrategy):
    """
    Estratégia personalizada para mapear planilhas que já seguem o layout interno
    esperado, garantindo tipos corretos e ordem de colunas.
    """

    def __init__(self, layout_config: dict[str, Any], mapeamento: dict[str, Any] | None = None):
        super().__init__(layout_config, mapeamento)

    def map_transactions(self, df_bruto: pd.DataFrame) -> pd.DataFrame:
        """
        Converte a aba de transações do usuário para o formato interno.
        - Garante que a coluna 'Data' esteja em datetime.
        - Garante que todas as colunas do layout interno existam e estejam na ordem correta.
        """
        coluna_data = "Data"
        if coluna_data in df_bruto.columns:
            try:
                df_bruto[coluna_data] = pd.to_datetime(df_bruto[coluna_data], errors="coerce")
            except Exception as e:
                print(f"AVISO (CustomStrategy): Falha ao converter '{coluna_data}' para datetime: {e}")

        # Utiliza o método genérico da base para ajustar colunas e ordem
        return self.map_other_sheet(df_bruto, config.NomesAbas.TRANSACOES)

    def unmap_transactions(self, df_interno: pd.DataFrame) -> pd.DataFrame:
        """
        Converte o DataFrame interno de volta para o layout original do usuário.
        Como o layout já corresponde ao interno, basta devolver as colunas
        definidas no layout, preservando a ordem.
        """
        colunas_para_salvar = [col for col in self.colunas_transacoes if col in df_interno.columns]
        return df_interno[colunas_para_salvar]