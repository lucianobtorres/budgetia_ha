# Em: src/finance/mapping_strategies/base_strategy.py

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

import config


class BaseMappingStrategy(ABC):
    """
    Interface (Classe Base Abstrata) para todas as estratégias de mapeamento.
    Define o "contrato" que o ExcelHandler espera.
    """

    def __init__(
        self, layout_config: dict[str, Any], mapeamento: dict[str, Any] | None = None
    ):
        """
        Inicializa a estratégia.

        Args:
            layout_config: O dicionário LAYOUT_PLANILHA do config.
            mapeamento: O dicionário 'mapeamento' (se aplicável).
        """
        self.layout_config = layout_config
        self.mapeamento = mapeamento if mapeamento is not None else {}
        self.colunas_transacoes = self.layout_config[config.NomesAbas.TRANSACOES]

    @abstractmethod
    def map_transactions(self, df_bruto: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe um DataFrame bruto da aba de transações do usuário
        e o transforma no DataFrame padrão do nosso sistema.

        Args:
            df_bruto: O DataFrame lido diretamente do arquivo Excel do usuário.

        Returns:
            Um novo DataFrame formatado com as colunas do
            config.NomesAbas.TRANSACOES.
        """
        pass

    @abstractmethod
    def unmap_transactions(self, df_interno: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe o DataFrame de transações no formato INTERNO do sistema
        e o "traduz de volta" para o formato ORIGINAL do usuário.

        Args:
            df_interno: O DataFrame no formato (config.LAYOUT_PLANILHA)

        Returns:
            Um DataFrame formatado como a planilha original do usuário.
        """
        pass

    def get_sheet_name_to_save(self, internal_sheet_name: str) -> str:
        """
        Retorna o nome da aba "real" onde os dados devem ser salvos.
        """
        if internal_sheet_name == config.NomesAbas.TRANSACOES:
            # Por padrão, pergunta ao mapa (se ele existir)
            return self.mapeamento.get("aba_transacoes", internal_sheet_name)
        return internal_sheet_name

    def map_other_sheet(self, df: pd.DataFrame, aba_nome: str) -> pd.DataFrame:
        """
        Método padrão para mapear outras abas (Orçamentos, Dívidas, etc.).
        Por padrão, apenas garante que as colunas do layout existam.
        """
        if aba_nome not in self.layout_config:
            return df  # Retorna como está se não conhecermos a aba

        colunas_padrao = self.layout_config[aba_nome]

        for col in colunas_padrao:
            if col not in df.columns:
                df[col] = pd.NA

        return df[colunas_padrao]  # Retorna ordenado e completo
