# src/finance/storage/google_sheets_storage_handler.py


import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe, set_with_dataframe

import config
from finance.storage.base_storage_handler import BaseStorageHandler
from finance.strategies.base_strategy import BaseMappingStrategy

# Define o caminho para a chave de serviço
CREDENTIALS_PATH = config.GSPREAD_CREDENTIALS_PATH
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleSheetsStorageHandler(BaseStorageHandler):
    """
    Implementação concreta do BaseStorageHandler que lê e escreve
    em uma Planilha Google (Google Sheets).
    """

    def __init__(self, spreadsheet_url_or_key: str):
        print(
            f"--- DEBUG (GSheetsHandler): __init__ chamado para: '{spreadsheet_url_or_key}' ---"
        )
        try:
            # Autentica usando a Conta de Serviço
            gc = gspread.service_account(filename=CREDENTIALS_PATH, scopes=SCOPES)

            # Abre a planilha (seja por URL ou pela Chave/ID)
            self.spreadsheet = gc.open_by_url(spreadsheet_url_or_key)
            self._is_new_file = False  # Assumimos que não é nova se conseguiu abrir
            print(
                f"--- DEBUG (GSheetsHandler): Planilha '{self.spreadsheet.title}' aberta com sucesso. ---"
            )

        except gspread.exceptions.SpreadsheetNotFound:
            print(
                "--- DEBUG (GSheetsHandler): Planilha NÃO encontrada. Assumindo nova. ---"
            )
            # Se não encontrou, criamos uma nova (ou tratamos o erro)
            # Por enquanto, vamos parar se não for encontrada
            raise ValueError(
                f"Planilha Google não encontrada ou não compartilhada: {spreadsheet_url_or_key}"
            )
        except Exception as e:
            print(f"ERRO (GSheetsHandler): Falha ao autenticar ou abrir planilha: {e}")
            raise

    @property
    def is_new_file(self) -> bool:
        """
        Verifica se a planilha é nova. Para GSheets, por enquanto,
        partimos do princípio que o usuário a cria e compartilha primeiro.
        """
        # A lógica de "novo arquivo" no GSheets é diferente.
        # O 'load_sheets' vai verificar se as *abas* existem.
        return self._is_new_file

    def load_sheets(
        self,
        layout_config: dict[str, list[str]],
        strategy: BaseMappingStrategy,
    ) -> tuple[dict[str, pd.DataFrame], bool]:
        """
        Carrega as abas da Planilha Google usando a Estratégia de Mapeamento.
        """
        print("\n--- [LOG GSheetsHandler] Iniciando load_sheets ---")
        dataframes: dict[str, pd.DataFrame] = {}
        is_new_file = False  # Flag para saber se *abas* estão faltando

        try:
            abas_existentes = [ws.title for ws in self.spreadsheet.worksheets()]

            # Itera sobre o layout padrão do sistema (Transacoes, Orcamentos...)
            for sheet_name_padrao, columns_padrao in layout_config.items():
                # Pergunta à estratégia qual o nome "real" da aba
                nome_aba_para_ler = strategy.get_sheet_name_to_save(sheet_name_padrao)

                df_bruto: pd.DataFrame

                if nome_aba_para_ler in abas_existentes:
                    print(
                        f"--- [LOG GSheetsHandler] Lendo aba: '{nome_aba_para_ler}' ---"
                    )
                    worksheet = self.spreadsheet.worksheet(nome_aba_para_ler)
                    # Usa gspread-dataframe para ler
                    df_bruto = get_as_dataframe(worksheet, evaluate_formulas=True)
                else:
                    print(
                        f"AVISO: Aba '{nome_aba_para_ler}' (padrão: '{sheet_name_padrao}') não encontrada."
                    )
                    df_bruto = pd.DataFrame()  # Cria vazio
                    is_new_file = True  # Marca que uma aba do sistema faltou

                # 1. Aplica a estratégia de mapeamento (tradução)
                if sheet_name_padrao == config.NomesAbas.TRANSACOES:
                    dataframes[sheet_name_padrao] = strategy.map_transactions(df_bruto)
                else:
                    dataframes[sheet_name_padrao] = strategy.map_other_sheet(
                        df_bruto, sheet_name_padrao
                    )

            self._is_new_file = is_new_file
            return dataframes, is_new_file

        except Exception as e:
            print(
                f"ERRO CRÍTICO ao ler o Google Sheets: {e}. Retornando estrutura vazia."
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
        add_intelligence: bool = False,  # (add_intelligence é mais complexo no GSheets)
    ) -> None:
        """
        Salva os DataFrames de volta na Planilha Google.
        """
        print("\n--- [LOG GSheetsHandler] Iniciando save_sheets ---")
        try:
            abas_existentes = [ws.title for ws in self.spreadsheet.worksheets()]

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
                    df_para_salvar = strategy.map_other_sheet(
                        df_interno, internal_sheet_name
                    )

                # 3. Pega ou Cria a aba
                worksheet: gspread.Worksheet
                if sheet_name_to_save not in abas_existentes:
                    print(
                        f"--- [LOG GSheetsHandler] Criando aba: '{sheet_name_to_save}' ---"
                    )
                    worksheet = self.spreadsheet.add_worksheet(
                        title=sheet_name_to_save, rows=100, cols=20
                    )
                else:
                    worksheet = self.spreadsheet.worksheet(sheet_name_to_save)

                # 4. Limpa e salva os dados usando gspread-dataframe
                worksheet.clear()
                # Converte tipos de dados que dão problema no JSON (como datas)
                df_para_salvar = df_para_salvar.astype(str).replace("NaT", "")

                set_with_dataframe(worksheet, df_para_salvar, resize=True)
                print(
                    f"--- [LOG GSheetsHandler] Aba '{sheet_name_to_save}' salva com sucesso. ---"
                )

        except Exception as e:
            print(f"ERRO CRÍTICO ao salvar no Google Sheets: {e}")
