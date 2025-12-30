# src/finance/storage/google_sheets_storage_handler.py


import gspread
import pandas as pd
from typing import Any
from gspread_dataframe import get_as_dataframe, set_with_dataframe

import config
from config import GSPREAD_CREDENTIALS_PATH, NomesAbas
from core.logger import get_logger
from finance.storage.base_storage_handler import BaseStorageHandler

logger = get_logger("GSheetsHandler")
from finance.strategies.base_strategy import BaseMappingStrategy

# Define o caminho para a chave de serviço
CREDENTIALS_PATH = config.GSPREAD_CREDENTIALS_PATH
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleSheetsStorageHandler(BaseStorageHandler): # type: ignore[misc]
    """
    Implementação concreta do BaseStorageHandler que lê e escreve
    em uma Planilha Google (Google Sheets).
    """

    def __init__(self, spreadsheet_url_or_key: str, credentials: Any | None = None):
        logger.debug(
            f"__init__ chamado para: '{spreadsheet_url_or_key}'"
        )
        try:
            gc = None
            # 1. Tenta usar credenciais de usuário explicitamente fornecidas (OAuth)
            if credentials:
                logger.debug("Usando CREDENCIAIS DE USUÁRIO fornecidas.")
                try:
                    gc = gspread.authorize(credentials)
                except Exception as e:
                    logger.warning(f"Falha ao autorizar com credenciais de usuário: {e}. Tentando Service Account...")

            # 2. Fallback: Autentica usando a Conta de Serviço (se não tiver user creds ou falhar)
            if not gc:
                logger.debug("Usando SERVICE ACCOUNT (Fallback/Default).")
                if Path(CREDENTIALS_PATH).exists():
                     gc = gspread.service_account(filename=CREDENTIALS_PATH, scopes=SCOPES)
                else:
                     raise FileNotFoundError(f"Credenciais de User vazias e Service Account não encontrada em {CREDENTIALS_PATH}")

            # Abre a planilha (seja por URL ou pela Chave/ID)
            self.spreadsheet = gc.open_by_url(spreadsheet_url_or_key)
            self._is_new_file = False  # Assumimos que não é nova se conseguiu abrir
            logger.debug(
                f"Planilha '{self.spreadsheet.title}' aberta com sucesso."
            )

        except gspread.exceptions.SpreadsheetNotFound:
            logger.debug(
                "Planilha NÃO encontrada. Assumindo nova."
            )
            # Se não encontrou, criamos uma nova (ou tratamos o erro)
            # Por enquanto, vamos parar se não for encontrada
            raise ValueError(
                f"Planilha Google não encontrada ou não compartilhada: {spreadsheet_url_or_key}"
            )
        except gspread.exceptions.APIError as e:
            if "400" in str(e) and "supported" in str(e):
                error_msg = (
                    "ERRO DE FORMATO: Você forneceu um link para um arquivo Excel (.xlsx) no Google Drive. "
                    "O sistema BudgetIA precisa de uma 'Planilha Google' nativa.\n"
                    "SOLUÇÃO: Abra seu arquivo no Google Drive, vá em 'Arquivo' -> 'Salvar como Planilha Google' "
                    "e use o novo link gerado."
                )
                logger.critical(f"{error_msg}")
                raise ValueError(error_msg)
            else:
                logger.error(f"Falha de API ao abrir planilha: {e}")
                raise
        except Exception as e:
            logger.error(f"Falha ao autenticar ou abrir planilha: {e}")
            raise

    @property
    def resource_id(self) -> str:
        """
        Retorna o ID Único da Planilha Google (Spreadsheet ID).
        Usado como chave para o Redis Lock.
        """
        try:
            return self.spreadsheet.id # type: ignore[attr-defined, no-any-return]
        except Exception:
            # Fallback se algo der errado (ex: não aberto ainda)
            return "unknown_gsheets_resource"

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
        logger.debug("Iniciando load_sheets")
        dataframes: dict[str, pd.DataFrame] = {}
        is_new_file = False  # Flag para saber se *abas* estão faltando

        try:
            abas_existentes = [ws.title for ws in self.spreadsheet.worksheets()]
            logger.debug(f"Abas encontradas na planilha: {abas_existentes}")

            # Itera sobre o layout padrão do sistema (Transacoes, Orcamentos...)
            for sheet_name_padrao, columns_padrao in layout_config.items():
                # Pergunta à estratégia qual o nome "real" da aba
                nome_aba_para_ler = strategy.get_sheet_name_to_save(sheet_name_padrao)

                df_bruto: pd.DataFrame

                if nome_aba_para_ler in abas_existentes:
                    logger.debug(
                        f"Lendo aba: '{nome_aba_para_ler}'"
                    )
                    worksheet = self.spreadsheet.worksheet(nome_aba_para_ler)
                    # Usa gspread-dataframe para ler
                    df_bruto = get_as_dataframe(worksheet, evaluate_formulas=True)
                else:
                    logger.warning(
                        f"Aba '{nome_aba_para_ler}' (padrão: '{sheet_name_padrao}') não encontrada."
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

            return dataframes, is_new_file

        except Exception as e:
            logger.critical(f"ERRO CRÍTICO ao carregar abas do Google Sheets: {e}")
            return {}, False

    def get_source_modified_time(self) -> str | None:
        """
        Retorna o timestamp 'updated' dos metadados da Planilha Google.
        """
        try:
            # Em gspread moderno, propriedades são carregadas automaticamente ou via fetch_sheet_metadata
            # Tentar acessar lastUpdateTime diretamente se disponível
            # Caso contrário, forçar refresh simula o fetch_properties antigo
            try:
                pass 
            except:
                pass

            # A propriedade 'updated' costumava vir do drive API, gspread mapeia alguns
            # Vamos tentar 'lastUpdateTime' se existir no modelo
            if hasattr(self.spreadsheet, 'lastUpdateTime'):
                 return str(self.spreadsheet.lastUpdateTime)
            
            # Se não, tentar via _properties que é o dict cru
            props = self.spreadsheet._properties
            if 'modifiedTime' in props:
                return str(props['modifiedTime'])
            
            return None
        except Exception as e:
            logger.warning(
                f"Não foi possível obter modifiedTime (updated) do GSheet: {e}"
            )
            return None

    def _retry_on_quota_error(self, func, *args, **kwargs):
        """
        Executa uma função com retry automático para erros de cota (429).
        """
        import time
        max_retries = 5
        base_wait = 2.0  # segundos

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except gspread.exceptions.APIError as e:
                # Verifica se é erro de cota (429) ou 'Quota exceeded'
                if e.response.status_code == 429 or "Quota exceeded" in str(e):
                    wait_time = base_wait * (2 ** attempt)  # Backoff exponencial: 2, 4, 8...
                    logger.warning(f"Cota excedida (429). Tentativa {attempt+1}/{max_retries}. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise  # Se não for erro de cota, explode normal
            except Exception as e:
                # Se for outro erro, explode
                raise e
        
        # Se esgotou as tentativas
        raise TimeoutError("Falha após múltiplas tentativas de superar erro de cota (429).")

    def save_sheets(
        self,
        dataframes: dict[str, pd.DataFrame],
        strategy: BaseMappingStrategy,
        add_intelligence: bool = False,  # (add_intelligence é mais complexo no GSheets)
    ) -> None:
        """
        Salva os DataFrames de volta na Planilha Google.
        """
        logger.debug("Iniciando save_sheets")
        try:
            # Pega lista de abas (com retry também, pois é chamada de API)
            abas_existentes = self._retry_on_quota_error(lambda: [ws.title for ws in self.spreadsheet.worksheets()])

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
                    logger.info(
                        f"Criando aba: '{sheet_name_to_save}'"
                    )
                    # Retry na criação
                    worksheet = self._retry_on_quota_error(
                        self.spreadsheet.add_worksheet,
                        title=sheet_name_to_save, rows=100, cols=20
                    )
                else:
                    # Retry na obtenção
                    worksheet = self._retry_on_quota_error(self.spreadsheet.worksheet, sheet_name_to_save)

                # --- 4. SAFE SAVE GUARD (Proteção contra Wipe) ---
                if df_para_salvar.empty or len(df_para_salvar) == 0:
                    # Verifica se a aba atual TEM dados
                    # (Tenta pegar A1 para ver se não está vazia, sem gastar muita cota)
                    try:
                        cell_a1 = self._retry_on_quota_error(worksheet.acell, 'A1')
                        has_data =  cell_a1.value is not None and cell_a1.value != ""
                    except:
                        # Se der erro ou não tiver A1, vamos assumir que pode ter dados por segurança
                        # ou tentar row_count (mas row_count sempre tem valor)
                        # Vamos tentar get_all_values limitados? Não, gasta cota.
                        # Melhor: Se A1 está vazio, chance alta de ser vazia.
                        has_data = False 
                    
                    if has_data:
                        logger.warning(f"[PROTECTION] ABORTANDO SALVAMENTO na aba '{sheet_name_to_save}'.")
                        logger.warning(f"[PROTECTION] MOTIVO: O DataFrame interno está VAZIO, mas a aba destino NÃO está.")
                        logger.warning(f"[PROTECTION] Isso previne perda de dados acidental. Verifique se o carregamento falhou.")
                        continue # Pula para a próxima aba, NÃO limpa e não salva essa

                # 5. Limpa e salva os dados usando gspread-dataframe (com retry)
                def save_operation():
                    worksheet.clear()
                    # Converte tipos de dados que dão problema no JSON (como datas)
                    df_str = df_para_salvar.astype(str).replace("NaT", "")
                    set_with_dataframe(worksheet, df_str, resize=True)
                
                self._retry_on_quota_error(save_operation)
                
                logger.info(
                    f"Aba '{sheet_name_to_save}' salva com sucesso."
                )

        except Exception as e:
            logger.critical(f"ERRO CRÍTICO ao salvar no Google Sheets: {e}")

    def ping(self) -> tuple[bool, str]:
        """Verifica se a planilha GSheet está acessível e compartilhada."""
        try:
            # A chamada .title é uma chamada de API leve que
            # falhará se não tivermos mais permissão.
            _ = self.spreadsheet.title
            return True, "Planilha Google acessível."
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 403:
                return (
                    False,
                    "Erro de Permissão (403): A Planilha Google não está mais compartilhada com o BudgetIA.",
                )
            return False, f"Erro de API do Google: {e}"
        except Exception as e:
            return False, f"Erro inesperado de conexão com GSheets: {e}"

