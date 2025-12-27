from typing import Optional

from finance.storage.base_storage_handler import BaseStorageHandler
from finance.storage.excel_storage_handler import ExcelStorageHandler
from finance.storage.google_drive_handler import GoogleDriveFileHandler
from finance.storage.google_sheets_storage_handler import GoogleSheetsStorageHandler
from finance.storage.storage_enums import StorageType


class StorageHandlerFactory:
    """
    Fábrica para criar instâncias de handlers de armazenamento.
    Detecta automaticamente o tipo de storage baseado no path/URL.
    """

    _REGISTRY: dict[StorageType, type[BaseStorageHandler]] = {
        StorageType.LOCAL_EXCEL: ExcelStorageHandler,
        StorageType.GOOGLE_DRIVE_FILE: GoogleDriveFileHandler,
        StorageType.GOOGLE_SHEETS: GoogleSheetsStorageHandler,
    }

    @staticmethod
    def _detect_storage_type(path: str) -> StorageType:
        """
        Detecta automaticamente o tipo de storage baseado no path/URL.

        Args:
            path: Caminho ou URL do arquivo de armazenamento.

        Returns:
            O tipo de storage detectado.
        """
        path_lower: str = path.lower()

        # Google Drive File (Excel no Drive)
        if "drive.google.com/file" in path_lower:
            return StorageType.GOOGLE_DRIVE_FILE

        # Google Sheets (arquivo nativo do Sheets)
        if "docs.google.com/spreadsheets" in path_lower:
            # Se tem 'sd=true' é um link de visualização para um Excel no Drive
            if "sd=true" in path_lower:
                return StorageType.GOOGLE_DRIVE_FILE
            return StorageType.GOOGLE_SHEETS

        # Arquivo local (.xlsx)
        return StorageType.LOCAL_EXCEL

    @classmethod
    def create_handler(cls, path: str) -> BaseStorageHandler:
        """
        Cria o handler apropriado baseado no path fornecido.

        Args:
            path: Caminho ou URL do arquivo de armazenamento.

        Returns:
            Instância do handler apropriado para o tipo de storage.

        Raises:
            ValueError: Se o tipo de storage não for suportado ou registrado.
        """
        storage_type: StorageType = cls._detect_storage_type(path)
        handler_class: Optional[type[BaseStorageHandler]] = cls._REGISTRY.get(
            storage_type
        )

        if not handler_class:
            raise ValueError(
                f"Tipo de storage '{storage_type}' não suportado ou não registrado."
            )

        # Instancia com os parâmetros apropriados para cada tipo
        if storage_type == StorageType.LOCAL_EXCEL:
            return handler_class(file_path=path)
        elif storage_type == StorageType.GOOGLE_DRIVE_FILE:
            return handler_class(file_url=path)
        elif storage_type == StorageType.GOOGLE_SHEETS:
            return handler_class(spreadsheet_url_or_key=path)
        else:
            raise ValueError(f"Handler para tipo '{storage_type}' não implementado.")

    @classmethod
    def get_available_storage_types(cls) -> list[StorageType]:
        """
        Retorna a lista de tipos de storage disponíveis.

        Returns:
            Lista com todos os tipos de storage suportados.
        """
        return list(cls._REGISTRY.keys())
