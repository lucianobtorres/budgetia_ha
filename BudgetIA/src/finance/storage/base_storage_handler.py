# src/finance/storage/base_storage_handler.py
from abc import ABC, abstractmethod

import pandas as pd

# Importa a interface da Estratégia, pois os métodos dependem dela
from finance.strategies.base_strategy import BaseMappingStrategy


class BaseStorageHandler(ABC):
    """
    Interface (Contrato) que define como o DataContext
    deve interagir com qualquer fonte de dados (Excel, GSheets, DB).

    Os métodos são baseados no ExcelHandler original.
    """

    # --- O ERRO ESTAVA AQUI ---
    # Removido o @property @abstractmethod para is_new_file.
    # Vamos confiar que a implementação (ExcelHandler)
    # definirá 'self.is_new_file' em seu __init__,
    # o que o seu código JÁ FAZ.
    # --- FIM DA CORREÇÃO ---

    @abstractmethod
    def load_sheets(
        self,
        layout_config: dict[str, list[str]],
        strategy: BaseMappingStrategy,
    ) -> tuple[dict[str, pd.DataFrame], bool]:
        """
        Carrega todas as abas, aplicando a estratégia de mapeamento
        fornecida para traduzir os dados para o formato interno.
        """
        pass

    @abstractmethod
    def save_sheets(
        self,
        dataframes: dict[str, pd.DataFrame],
        strategy: BaseMappingStrategy,
        add_intelligence: bool = False,
    ) -> None:
        """
        Salva todos os dataframes, aplicando a estratégia de mapeamento
        para "traduzir de volta" para o formato do usuário.
        """
        pass

    @abstractmethod
    def ping(self) -> tuple[bool, str]:
        """
        Verifica se o recurso de armazenamento (arquivo/link) está acessível.
        Retorna (True, "Sucesso") ou (False, "Mensagem de Erro").
        """
        pass

    @abstractmethod
    def get_source_modified_time(self) -> str | None:
        """
        Retorna o timestamp da "última modificação" do arquivo fonte.
        Deve ser uma chamada leve (apenas metadados).
        Retorna uma string (ISO format) ou None se não aplicável.
        """
        pass
