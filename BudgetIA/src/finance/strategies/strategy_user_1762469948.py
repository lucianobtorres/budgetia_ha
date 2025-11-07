from typing import Any

import pandas as pd

import config

from .base_strategy import BaseMappingStrategy


class CustomStrategy(BaseMappingStrategy):
    """
    Estratégia personalizada para o layout do usuário.
    Neste caso, o layout do usuário é idêntico ao formato interno do sistema.
    """

    def __init__(
        self, layout_config: dict[str, Any], mapeamento: dict[str, Any] | None = None
    ):
        super().__init__(layout_config, mapeamento)
        print("LOG: Estratégia 'CustomStrategy' selecionada.")

    def map_transactions(self, df_bruto: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe um DataFrame bruto da aba de transações do usuário
        e o transforma no DataFrame padrão do nosso sistema.
        Como o formato do usuário é idêntico ao formato interno,
        apenas garantimos que as colunas existam e estejam na ordem correta.
        """
        # Reutiliza a lógica genérica da classe base para garantir as colunas
        # e a ordem, adicionando colunas ausentes com NA se necessário.
        return self.map_other_sheet(df_bruto, config.NomesAbas.TRANSACOES)

    def unmap_transactions(self, df_interno: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe o DataFrame de transações no formato INTERNO do sistema
        e o "traduz de volta" para o formato ORIGINAL do usuário.
        Como o formato interno é idêntico ao formato original do usuário,
        apenas retornamos o DataFrame com as colunas esperadas.
        """
        # Filtra e ordena as colunas para corresponder exatamente ao layout
        # de transações definido no config.
        colunas_para_salvar = [
            col for col in self.colunas_transacoes if col in df_interno.columns
        ]

        # Retorna apenas as colunas definidas no layout, na ordem correta
        return df_interno[colunas_para_salvar]

    def get_sheet_name_to_save(self, internal_sheet_name: str) -> str:
        """
        Retorna o nome da aba "real" onde os dados devem ser salvos.
        Neste caso, os nomes das abas internas são os mesmos que os nomes
        das abas do usuário.
        """
        # A implementação padrão da classe base já lida com isso,
        # pois o nome da aba interna é o mesmo que o nome da aba do usuário.
        return super().get_sheet_name_to_save(internal_sheet_name)

    def map_other_sheet(self, df: pd.DataFrame, aba_nome: str) -> pd.DataFrame:
        """
        Mapeia outras abas (Orçamentos, Dívidas, etc.).
        Como o formato do usuário é idêntico ao formato interno para todas as abas,
        a implementação padrão da classe base é suficiente.
        """
        return super().map_other_sheet(df, aba_nome)