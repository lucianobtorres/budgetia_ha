import pytest

from finance.storage.excel_storage_handler import ExcelHandler
from finance.storage.storage_enums import StorageType
from finance.storage.storage_factory import StorageHandlerFactory


class TestStorageHandlerFactory:
    """Testa a factory de storage handlers."""

    def test_detect_local_excel(self) -> None:
        """Testa detecção de arquivo Excel local."""
        path = "C:\\Users\\user\\planilha.xlsx"
        storage_type = StorageHandlerFactory._detect_storage_type(path)
        assert storage_type == StorageType.LOCAL_EXCEL

    def test_detect_google_drive_file(self) -> None:
        """Testa detecção de arquivo Excel no Google Drive."""
        path = "https://drive.google.com/file/d/1ABC123/view"
        storage_type = StorageHandlerFactory._detect_storage_type(path)
        assert storage_type == StorageType.GOOGLE_DRIVE_FILE

    def test_detect_google_sheets_native(self) -> None:
        """Testa detecção de Google Sheets nativo."""
        path = "https://docs.google.com/spreadsheets/d/1ABC123/edit"
        storage_type = StorageHandlerFactory._detect_storage_type(path)
        assert storage_type == StorageType.GOOGLE_SHEETS

    def test_detect_google_drive_excel_with_sd_true(self) -> None:
        """Testa detecção de Excel no Drive quando link tem sd=true."""
        path = "https://docs.google.com/spreadsheets/d/1ABC123/edit?sd=true"
        storage_type = StorageHandlerFactory._detect_storage_type(path)
        assert storage_type == StorageType.GOOGLE_DRIVE_FILE

    def test_create_local_excel_handler(self) -> None:
        """Testa criação de ExcelHandler para arquivo local."""
        path = "C:\\planilha.xlsx"
        handler = StorageHandlerFactory.create_handler(path)
        assert isinstance(handler, ExcelHandler)

    def test_get_available_storage_types(self) -> None:
        """Testa retorno dos tipos disponíveis."""
        types = StorageHandlerFactory.get_available_storage_types()
        assert StorageType.LOCAL_EXCEL in types
        assert StorageType.GOOGLE_DRIVE_FILE in types
        assert StorageType.GOOGLE_SHEETS in types
        assert len(types) == 3
