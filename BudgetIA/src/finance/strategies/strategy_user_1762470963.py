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

        # O mapeamento para o nome da aba de transações é o mesmo,
        # mas podemos explicitá-lo se quisermos.
        # self.mapeamento["aba_transacoes"] = "Visão Geral e Transações"

    def map_transactions(self, df_bruto: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe um DataFrame bruto da aba de transações do usuário
        e o transforma no DataFrame padrão do nosso sistema.

        Como o layout do usuário para transações é idêntico ao formato interno,
        apenas garantimos que as colunas estejam presentes e na ordem correta.
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
        # Filtra e ordena as colunas para corresponder ao layout original do usuário.
        # self.colunas_transacoes já contém as colunas na ordem correta.
        colunas_para_salvar = [
            col for col in self_interno.columns if col in self.colunas_transacoes
        ]

        return df_interno[colunas_para_salvar]

    # O método get_sheet_name_to_save da classe base já funciona corretamente
    # para este cenário, pois o nome da aba do usuário é o mesmo do sistema.
    # Não é necessário sobrescrevê-lo.

    # O método map_other_sheet da classe base também funciona corretamente
    # para as outras abas, pois seus layouts também são idênticos.
    # Não é necessário sobrescrevê-lo.