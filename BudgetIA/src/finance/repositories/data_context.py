# src/finance/repositories/data_context.py

import pandas as pd

import config

from ..storage.base_storage_handler import BaseStorageHandler
from ..strategies.base_strategy import BaseMappingStrategy


class FinancialDataContext:
    """
    Mantém o estado dos dados em memória e coordena com o
    Handler de armazenamento (Excel, GSheets, etc.) e a Estratégia
    de Mapeamento (Default, Custom).
    """

    def __init__(
        self,
        storage_handler: BaseStorageHandler,
        strategy: BaseMappingStrategy,  # <-- Aceita a ESTRATÉGIA, não o 'mapeamento'
    ) -> None:
        """
        Inicializa o contexto.

        Args:
            storage_handler (BaseStorageHandler): O handler de armazenamento
                (Ex: ExcelHandler).
            mapeamento (dict | None): O mapa de usuário (se existir).
        """
        # --- 4. RENOMEAR O ATRIBUTO INTERNO ---
        self.storage = storage_handler
        self.layout_config = config.LAYOUT_PLANILHA

        self.strategy = strategy  # <-- Salva a estratégia injetada
        print(
            f"--- [LOG DataContext] Usando estratégia injetada: '{type(self.strategy).__name__}'."
        )

        self.data: dict[str, pd.DataFrame] = {}
        self.is_new_file = self._load_data()

    def _load_data(self) -> bool:
        """
        Usa o handler e a estratégia para carregar os dados.
        """
        # --- 5. USAR O NOVO ATRIBUTO 'self.storage' ---
        dataframes, is_new_file = self.storage.load_sheets(
            self.layout_config, self.strategy
        )
        self.data = dataframes
        return bool(is_new_file)

    def get_dataframe(self, sheet_name: str) -> pd.DataFrame:
        """
        Obtém um DataFrame do contexto pelo nome padrão (interno).
        """
        if sheet_name not in self.data:
            raise ValueError(f"Aba '{sheet_name}' não encontrada no contexto.")
        return self.data[sheet_name].copy()

    def update_dataframe(self, sheet_name: str, new_df: pd.DataFrame) -> None:
        """
        Atualiza um DataFrame no contexto pelo nome padrão (interno).
        """
        if sheet_name not in self.data:
            raise ValueError(f"Aba '{sheet_name}' não pode ser atualizada.")
        self.data[sheet_name] = new_df

    def save(self, add_intelligence: bool = False) -> None:
        """
        Salva TODOS os DataFrames em memória de volta no
        arquivo de origem (Excel), usando o handler.
        """
        # --- 6. USAR O NOVO ATRIBUTO 'self.storage' ---
        self.storage.save_sheets(self.data, self.strategy, add_intelligence)
