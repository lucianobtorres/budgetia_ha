from enum import Enum


class StorageType(str, Enum):
    """
    Enum para os tipos de armazenamento suportados.
    """

    LOCAL_EXCEL = "local_excel"
    GOOGLE_DRIVE_FILE = "google_drive_file"
    GOOGLE_SHEETS = "google_sheets"
