# src/finance/storage/google_drive_file_handler.py
import io
import re

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import (
    MediaIoBaseDownload,  # Para o Download (load_sheets)
    MediaIoBaseUpload,  # <--- CORREÇÃO: Usar esta para Upload
)

import config
from finance.storage.base_storage_handler import BaseStorageHandler
from finance.strategies.base_strategy import BaseMappingStrategy

# Define o caminho para a chave de serviço (reutilizando a mesma)
CREDENTIALS_PATH = config.GSPREAD_CREDENTIALS_PATH

# --- ATENÇÃO: ESCOPO DIFERENTE ---
# Precisamos de permissão total de 'drive' para ler/escrever
# arquivos que não foram criados pelo próprio app.
SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleDriveFileHandler(BaseStorageHandler):
    """
    Implementação do BaseStorageHandler para arquivos Excel (.xlsx)
    armazenados diretamente no Google Drive.
    """

    def __init__(self, file_url: str):
        print(f"--- DEBUG (GDriveHandler): __init__ chamado para: '{file_url}' ---")
        self.file_url = file_url
        self.file_id = self._extract_file_id(file_url)
        if not self.file_id:
            msg = f"URL do Google Drive inválida. Não foi possível extrair o File ID: {file_url}"
            print(msg)
            raise ValueError(msg)

        try:
            # --- CORREÇÃO DA AUTENTICAÇÃO ---
            # 1. Carrega as credenciais diretamente da biblioteca google.oauth2
            creds: Credentials = Credentials.from_service_account_file(
                CREDENTIALS_PATH, scopes=SCOPES
            )

            # 2. Constrói o serviço passando o objeto 'creds' (que o 'build' entende)
            self.drive_service = build("drive", "v3", credentials=creds)
            # --- FIM DA CORREÇÃO ---

            # Verifica se o arquivo existe (apenas para definir self._is_new_file)
            self.drive_service.files().get(fileId=self.file_id, fields="id").execute()
            self._is_new_file = False
            print(
                f"--- DEBUG (GDriveHandler): Serviço do Drive v3 construído. File ID: {self.file_id} ---"
            )

        except HttpError as e:
            if e.resp.status == 404:
                print(
                    f"ERRO (GDriveHandler): Arquivo NÃO encontrado no Drive: {self.file_id}"
                )
                raise ValueError(
                    f"Arquivo não encontrado ou sem permissão no Google Drive: {self.file_id}"
                )
            else:
                print(f"ERRO (GDriveHandler): Erro Http: {e}")
                raise
        except Exception as e:
            print(f"ERRO (GDriveHandler): Falha ao construir serviço do Drive: {e}")
            raise

    def _extract_file_id(self, url: str) -> str | None:
        """Extrai o ID do arquivo de uma URL do Google Drive."""
        # --- REGEX ATUALIZADO ---
        # Procura por "/file/d/ID" OU "/spreadsheets/d/ID"
        match = re.search(r"/(?:file|spreadsheets)/d/([a-zA-Z0-9_-]+)", url)
        # (?:...) -> é um grupo "não-capturável" (non-capturing group)
        # (file|spreadsheets) -> que aceita 'file' OU 'spreadsheets'
        # --- FIM DA ATUALIZAÇÃO ---
        if match:
            return match.group(1)
        return None

    @property
    def is_new_file(self) -> bool:
        """Retorna se o arquivo é considerado novo (não encontrado)."""
        return self._is_new_file

    def load_sheets(
        self,
        layout_config: dict[str, list[str]],
        strategy: BaseMappingStrategy,
    ) -> tuple[dict[str, pd.DataFrame], bool]:
        """
        Baixa o arquivo .xlsx do Google Drive em memória, carrega todas
        as abas, e aplica a Estratégia de Mapeamento.
        """
        print(f"--- [LOG GDriveHandler] Baixando arquivo: {self.file_id} ---")
        dataframes: dict[str, pd.DataFrame] = {}

        try:
            request = self.drive_service.files().get_media(fileId=self.file_id)

            # Cria um buffer de bytes em memória para receber o arquivo
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download: {int(status.progress() * 100)}%.")

            print(
                "--- [LOG GDriveHandler] Download concluído. Lendo Excel em memória... ---"
            )
            file_buffer.seek(0)

            # Lê o arquivo Excel (em memória) com pandas
            # sheet_name=None garante que TODAS as abas sejam lidas
            raw_sheets_data = pd.read_excel(
                file_buffer,
                sheet_name=None,
                engine="openpyxl",  # openpyxl precisa estar no pyproject.toml
            )

            # --- Lógica de Aplicação da Estratégia (copiada do GSheetsHandler) ---
            # Itera sobre o layout padrão do sistema
            for sheet_name_padrao, columns_padrao in layout_config.items():
                # Pergunta à estratégia qual o nome "real" da aba no Excel
                nome_aba_para_ler = strategy.get_sheet_name_to_save(sheet_name_padrao)

                df_bruto: pd.DataFrame
                if nome_aba_para_ler in raw_sheets_data:
                    df_bruto = raw_sheets_data[nome_aba_para_ler]
                else:
                    print(
                        f"AVISO: Aba '{nome_aba_para_ler}' (padrão: '{sheet_name_padrao}') não encontrada no Excel."
                    )
                    df_bruto = pd.DataFrame()
                    self._is_new_file = True  # Marca que abas estão faltando

                # Aplica a estratégia de mapeamento (tradução)
                if sheet_name_padrao == config.NomesAbas.TRANSACOES:
                    dataframes[sheet_name_padrao] = strategy.map_transactions(df_bruto)
                else:
                    dataframes[sheet_name_padrao] = strategy.map_other_sheet(
                        df_bruto, sheet_name_padrao
                    )
            # --- Fim da Lógica da Estratégia ---

            return dataframes, self._is_new_file

        except Exception as e:
            print(
                f"ERRO CRÍTICO ao ler o arquivo do GDrive: {e}. Retornando estrutura vazia."
            )
            # Fallback: cria estrutura vazia em memória
            for sheet_name, columns in layout_config.items():
                dataframes[sheet_name] = pd.DataFrame(columns=columns)
            self._is_new_file = True
            return dataframes, True

    def save_sheets(
        self,
        dataframes: dict[str, pd.DataFrame],
        strategy: BaseMappingStrategy,
        add_intelligence: bool = False,  # (add_intelligence não é aplicado aqui)
    ) -> None:
        """
        Salva os DataFrames de volta no arquivo .xlsx no Google Drive.
        """
        print(
            f"--- [LOG GDriveHandler] Preparando para salvar (upload) arquivo: {self.file_id} ---"
        )

        try:
            # Cria um buffer de bytes em memória
            output_buffer = io.BytesIO()

            # Escreve todos os DataFrames no buffer usando ExcelWriter
            with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
                # Lógica de "unmap" da Estratégia (copiada do GSheetsHandler)
                for internal_sheet_name, df_interno in dataframes.items():
                    # 1. Pergunta à estratégia o nome real da aba
                    sheet_name_to_save = strategy.get_sheet_name_to_save(
                        internal_sheet_name
                    )

                    # 2. Pergunta à estratégia para "traduzir de volta"
                    df_para_salvar: pd.DataFrame
                    if internal_sheet_name == config.NomesAbas.TRANSACOES:
                        df_para_salvar = strategy.unmap_transactions(df_interno)
                    else:
                        # ERRO SUTIL CORRIGIDO: GSheetsHandler usa map_other_sheet aqui
                        # mas deveríamos usar 'unmap_other_sheet' (se existir)
                        # ou uma lógica inversa. Vou seguir seu padrão por enquanto:
                        df_para_salvar = strategy.map_other_sheet(
                            df_interno, internal_sheet_name
                        )

                    # 3. Escreve no ExcelWriter em memória
                    df_para_salvar.to_excel(
                        writer, sheet_name=sheet_name_to_save, index=False
                    )

            # Rebovina o buffer
            output_buffer.seek(0)

            # Prepara a mídia para o upload
            media_body = MediaIoBaseUpload(
                output_buffer,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resumable=True,
            )

            # Executa a atualização (upload) do arquivo
            updated_file = (
                self.drive_service.files()
                .update(fileId=self.file_id, media_body=media_body, fields="id, name")
                .execute()
            )

            print(
                f"--- [LOG GDriveHandler] Arquivo '{updated_file.get('name')}' atualizado no Drive! ---"
            )

        except Exception as e:
            print(f"Erro ao salvar (upload) o arquivo para o Google Drive: {e}")
            raise

    def ping(self) -> tuple[bool, str]:
        """Verifica se o arquivo GDrive está acessível."""
        try:
            # Uma chamada 'get' apenas de metadados é a mais leve possível
            self.drive_service.files().get(fileId=self.file_id, fields="id").execute()
            return True, "Arquivo Google Drive acessível."
        except HttpError as e:
            if e.resp.status == 403:
                return (
                    False,
                    "Erro de Permissão (403): O arquivo no Google Drive não está mais compartilhado com o BudgetIA.",
                )
            elif e.resp.status == 404:
                return (
                    False,
                    "Erro (404): O arquivo no Google Drive foi movido ou excluído.",
                )
            return False, f"Erro HTTP do Google Drive: {e}"
        except Exception as e:
            return False, f"Erro inesperado de conexão com GDrive: {e}"
