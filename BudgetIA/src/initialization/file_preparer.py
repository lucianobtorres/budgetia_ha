# src/initialization/file_preparer.py
import os
from pathlib import Path

import magic
import pandas as pd
from googleapiclient.http import MediaIoBaseDownload
from gspread_dataframe import get_as_dataframe

# Importa do núcleo do sistema
import config
from finance.storage.google_drive_handler import GoogleDriveFileHandler
from finance.storage.google_sheets_storage_handler import GoogleSheetsStorageHandler

# O arquivo temporário que o StrategyGenerator usará
TEMP_ANALYSIS_FILE = Path(config.DATA_DIR) / "temp_analysis_file.xlsx"


class FileAnalysisPreparer:
    """
    Responsabilidade Única: Garantir que, dado um caminho (local ou link),
    um arquivo local exista para o StrategyGenerator analisar.
    Gerencia a criação e limpeza de arquivos temporários.
    """

    def __init__(self, path_str: str):
        self.path_str = path_str
        self._is_temp_file = False
        self._local_path_to_analyze: str = ""

    def _download_gdrive_excel(self) -> str:
        """Baixa um .xlsx do GDrive para o arquivo temporário."""
        print("--- DEBUG Preparer: Baixando GDrive Excel para análise... ---")
        handler = GoogleDriveFileHandler(file_url=self.path_str)
        request = handler.drive_service.files().get_media(fileId=handler.file_id)

        TEMP_ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TEMP_ANALYSIS_FILE, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

        print(
            f"--- DEBUG Preparer: Download de GDrive Excel concluído para '{TEMP_ANALYSIS_FILE}'. ---"
        )
        return str(TEMP_ANALYSIS_FILE)

    def _convert_gsheet_to_excel(self) -> str:
        """Converte uma GSheet nativa para um arquivo .xlsx temporário."""
        print("--- DEBUG Preparer: Lendo GSheet Nativo para análise... ---")
        handler = GoogleSheetsStorageHandler(spreadsheet_url_or_key=self.path_str)

        TEMP_ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(TEMP_ANALYSIS_FILE, engine="openpyxl") as writer:
            spreadsheet = handler.spreadsheet
            for aba in spreadsheet.worksheets():
                try:
                    print(f"--- DEBUG Preparer: Lendo aba GSheet '{aba.title}'... ---")
                    df_aba = get_as_dataframe(aba, evaluate_formulas=True)
                    df_aba.to_excel(writer, sheet_name=aba.title, index=False)
                except Exception as e:
                    print(
                        f"--- DEBUG Preparer: Falha ao ler aba '{aba.title}': {e}. Pulando... ---"
                    )
                    continue

        print(
            f"--- DEBUG Preparer: GSheet Nativo salvo em Excel temporário '{TEMP_ANALYSIS_FILE}'. ---"
        )
        return str(TEMP_ANALYSIS_FILE)

    def get_local_path(self) -> str:
        """
        Retorna o caminho local para o arquivo, baixando ou convertendo se necessário.
        """
        self._is_temp_file = False

        if self.path_str.startswith("http://") or self.path_str.startswith("https://"):
            self._is_temp_file = True  # Marcar para limpeza

            # CASO A: GDrive Excel
            if ("drive.google.com/file" in self.path_str) or (
                "docs.google.com/spreadsheets" in self.path_str
                and "sd=true" in self.path_str
            ):
                self._local_path_to_analyze = self._download_gdrive_excel()

            # CASO B: GSheet Nativo
            elif "docs.google.com/spreadsheets" in self.path_str:
                self._local_path_to_analyze = self._convert_gsheet_to_excel()

            else:
                raise ValueError(
                    "Link inválido. Deve ser do Google Drive ou Google Sheets."
                )

        else:
            # CASO C: Arquivo Local
            self._local_path_to_analyze = self.path_str

        # --- INÍCIO DA CAMADA DE SEGURANÇA ---
        try:
            if not Path(self._local_path_to_analyze).exists():
                raise ValueError(
                    "Arquivo local não encontrado (pode ter falhado o download)."
                )

            # Lê os "magic bytes" para ver o tipo real do arquivo
            mime_type = magic.from_file(self._local_path_to_analyze, mime=True)

            tipos_permitidos = [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
                "application/zip",  # .xlsx às vezes é visto como zip
            ]

            if mime_type not in tipos_permitidos:
                raise ValueError(
                    f"Tipo de arquivo inseguro ou inválido detectado: {mime_type}"
                )

            print(
                f"--- DEBUG Preparer: Verificação de arquivo OK. MIME: {mime_type} ---"
            )

        except Exception as e:
            # Se falhar, limpa o temporário (se houver) e levanta o erro
            self.cleanup()
            raise ValueError(f"Falha na preparação do arquivo: {e}")
        # --- FIM DA CAMADA DE SEGURANÇA ---

        return self._local_path_to_analyze
        return self._local_path_to_analyze

    def cleanup(self) -> None:
        """Remove o arquivo temporário, se um foi criado."""
        if self._is_temp_file and TEMP_ANALYSIS_FILE.exists():
            try:
                os.remove(TEMP_ANALYSIS_FILE)
                print(
                    f"--- DEBUG Preparer: Arquivo temporário '{TEMP_ANALYSIS_FILE}' removido. ---"
                )
            except OSError as e:
                print(
                    f"--- DEBUG Preparer: Não foi possível remover o arquivo temporário: {e} ---"
                )
