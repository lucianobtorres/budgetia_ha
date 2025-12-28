# src/finance/repositories/data_context.py

import pandas as pd

import config
from infrastructure.caching.redis_cache_service import RedisCacheService

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
        strategy: BaseMappingStrategy,
        cache_service: RedisCacheService,
        cache_key: str,
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

        self.strategy = strategy
        self.cache = cache_service
        self.cache_key = cache_key
        print(
            f"--- [LOG DataContext] Usando estratégia injetada: '{type(self.strategy).__name__}'."
        )

        self.is_cache_hit = False
        self.data: dict[str, pd.DataFrame] = {}
        self.is_new_file = self._load_data()

    def _load_data(self) -> bool:
        """
        Usa o handler e a estratégia para carregar os dados.
        """
        cached_data, cached_timestamp = self.cache.get_entry(self.cache_key)
        source_timestamp = self.storage.get_source_modified_time()

        # --- 3. DECIDIR (O SEU INSIGHT) ---
        if cached_data is not None and cached_timestamp == source_timestamp:
            print(
                "--- [LOG DataContext] Cache HIT (Timestamps correspondem). Carregando dados do Redis. ---"
            )
            self.data = cached_data
            self.is_cache_hit = True
            return False

        if cached_data is not None:
            print(
                f"--- [LOG DataContext] Cache STALE (Timestamps diferem: {cached_timestamp} != {source_timestamp}). ---"
            )
        else:
            print("--- [LOG DataContext] Cache MISS (Vazio). ---")

        print("Lendo do armazenamento (GSheets/Excel)...")
        dataframes, is_new_file = self.storage.load_sheets(
            self.layout_config, self.strategy
        )
        self.data = dataframes

        self.is_cache_hit = False
        if not is_new_file:
            final_source_timestamp = self.storage.get_source_modified_time()
            self.cache.set_entry(self.cache_key, self.data, final_source_timestamp)

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
        # 1. Salva no GDrive/Excel (lento)
        print("LOG: Salvando no armazenamento persistente (StorageHandler)...")
        self.storage.save_sheets(self.data, self.strategy, add_intelligence)

        try:
            # Espera 1s para garantir que o GDrive atualize seus metadados
            import time

            time.sleep(1)
        except:
            pass  # (Não é crítico se o sleep falhar)

        final_source_timestamp = self.storage.get_source_modified_time()

        # 3. Atualiza o cache (rápido)
        print("LOG: Atualizando o cache (CacheService)...")
        self.cache.set_entry(self.cache_key, self.data, final_source_timestamp)

        print("LOG: Salvamento e atualização de cache concluídos.")
