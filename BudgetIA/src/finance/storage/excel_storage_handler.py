# Em: src/finance/storage/excel_storage_handler.py
import os

import pandas as pd

import config  # Importar config para NomesAbas
from config import (
    ColunasDividas,
    ColunasMetas,
    ColunasOrcamentos,
    ColunasTransacoes,
)

# --- 1. IMPORTAR A INTERFACE CORRIGIDA ---
from finance.storage.base_storage_handler import BaseStorageHandler
from finance.strategies.base_strategy import BaseMappingStrategy


# --- 2. FAZER A CLASSE HERDAR DA INTERFACE ---
class ExcelHandler(BaseStorageHandler):
    """Classe especialista em ler e escrever DataFrames para um arquivo Excel."""

    def __init__(self, file_path: str) -> None:
        # --- LOG ADICIONADO ---
        print(
            f"--- DEBUG (ExcelHandler): __init__ chamado com file_path: '{file_path}' ---"
        )
        # --- FIM DO LOG ---

        self.file_path = file_path

        # --- LOG ADICIONADO ---
        file_exists = os.path.exists(self.file_path)
        print(
            f"--- DEBUG (ExcelHandler): 'os.path.exists' para '{self.file_path}' retornou: {file_exists} ---"
        )
        # --- FIM DO LOG ---

        # --- 3. DEFINIÇÃO DO ATRIBUTO (PERFEITO, NÃO PRECISA MUDAR) ---
        # A flag is_new_file será determinada pelo load_sheets
        self.is_new_file = not os.path.exists(self.file_path)

    def load_sheets(
        self,
        layout_config: dict[str, list[str]],
        strategy: BaseMappingStrategy,  # <-- Agora recebe a ESTRATÉGIA
    ) -> tuple[dict[str, pd.DataFrame], bool]:
        """
        Carrega as abas da planilha usando a Estratégia de Mapeamento fornecida.
        Removemos toda a lógica 'if mapeamento:' daqui.
        """

        # --- LOG INICIAL ---
        print("\n--- [LOG ExcelHandler] Iniciando load_sheets ---")
        print(f"--- [LOG ExcelHandler] Verificando arquivo: {self.file_path} ---")

        dataframes: dict[str, pd.DataFrame] = {}
        is_new_file = self.is_new_file  # Pega o estado inicial

        # --- LOG ADICIONADO ---
        print(
            f"--- DEBUG (ExcelHandler): 'load_sheets' iniciando. 'is_new_file' (do self) é: {is_new_file} ---"
        )
        # --- FIM DO LOG ---

        if is_new_file:
            print(
                f"AVISO: Arquivo '{self.file_path}' não encontrado. Estrutura criada em memória."
            )
            # Cria DataFrames vazios para todas as abas do layout
            for sheet_name, columns in layout_config.items():
                dataframes[sheet_name] = pd.DataFrame(columns=columns)
        else:
            print(f"LOG: Carregando planilha existente de '{self.file_path}'.")
            try:
                xls = pd.ExcelFile(self.file_path)
                abas_existentes = xls.sheet_names

                # 1. Carrega a aba de TRANSAÇÕES usando a estratégia
                # A estratégia nos diz qual o nome real da aba
                nome_aba_transacoes = strategy.get_sheet_name_to_save(
                    config.NomesAbas.TRANSACOES
                )

                df_bruto_transacoes: pd.DataFrame
                if nome_aba_transacoes in abas_existentes:
                    df_bruto_transacoes = pd.read_excel(
                        xls, sheet_name=nome_aba_transacoes
                    )
                else:
                    # Se a aba principal falta, trata como arquivo incompleto
                    print(
                        f"AVISO: Aba de transações '{nome_aba_transacoes}' não encontrada."
                    )
                    df_bruto_transacoes = pd.DataFrame(
                        columns=strategy.colunas_transacoes
                    )
                    is_new_file = True

                # Delega a tradução (mágica acontece aqui)
                dataframes[config.NomesAbas.TRANSACOES] = strategy.map_transactions(
                    df_bruto_transacoes
                )

                # 2. Carrega as OUTRAS abas (Orçamentos, Dívidas, etc.)
                for sheet_name_padrao, columns in layout_config.items():
                    # Pula a aba de transações que já carregamos
                    if sheet_name_padrao == config.NomesAbas.TRANSACOES:
                        continue

                    nome_aba_para_ler = strategy.get_sheet_name_to_save(
                        sheet_name_padrao
                    )

                    df_bruto_outra: pd.DataFrame
                    if sheet_name_padrao in abas_existentes:
                        df_bruto_outra = pd.read_excel(
                            xls, sheet_name=nome_aba_para_ler
                        )
                    else:
                        print(
                            f"AVISO: Aba do sistema '{sheet_name_padrao}' não encontrada. Criando vazia."
                        )
                        df_bruto_outra = pd.DataFrame(columns=columns)
                        is_new_file = True  # Marca para salvar

                    # Delega a garantia das colunas (map_other_sheet)
                    dataframes[sheet_name_padrao] = strategy.map_other_sheet(
                        df_bruto_outra, sheet_name_padrao
                    )

            except Exception as e:
                print(
                    f"ERRO CRÍTICO ao ler o arquivo Excel: {e}. Criando estrutura do zero em memória."
                )
                is_new_file = True
                for sheet_name, columns in layout_config.items():
                    dataframes[sheet_name] = pd.DataFrame(columns=columns)

        self.is_new_file = is_new_file
        return dataframes, is_new_file

    def save_sheets(
        self,
        dataframes: dict[str, pd.DataFrame],
        strategy: BaseMappingStrategy,  # <-- Agora recebe a ESTRATÉGIA
        add_intelligence: bool = False,
    ) -> None:
        """
        Salva os DataFrames em um arquivo Excel, usando a Estratégia
        para "traduzir de volta" os dados para o formato do usuário.
        """
        try:
            with pd.ExcelWriter(self.file_path, engine="xlsxwriter") as writer:
                for internal_sheet_name, df_interno in dataframes.items():
                    # 1. Pergunta à estratégia qual o nome "real" da aba para salvar
                    sheet_name_to_save = strategy.get_sheet_name_to_save(
                        internal_sheet_name
                    )

                    df_para_salvar: pd.DataFrame

                    # 2. Pergunta à estratégia para "traduzir de volta" o DataFrame
                    if internal_sheet_name == config.NomesAbas.TRANSACOES:
                        df_para_salvar = strategy.unmap_transactions(df_interno)
                    else:
                        # Outras abas (Orçamento, Dívidas) são salvas como estão
                        df_para_salvar = strategy.map_other_sheet(
                            df_interno, internal_sheet_name
                        )

                    # 3. Tratar NaT (Not a Time) antes de salvar
                    for col in df_para_salvar.select_dtypes(
                        include=["datetime64[ns]"]
                    ).columns:
                        df_para_salvar[col] = (
                            df_para_salvar[col]
                            .astype(object)
                            .where(df_para_salvar[col].notna(), None)
                        )

                    # 4. Salva o DataFrame traduzido na aba correta
                    df_para_salvar.to_excel(
                        writer, sheet_name=sheet_name_to_save, index=False
                    )

                    # 5. Aplica formatação (apenas se for nosso layout padrão)
                    if add_intelligence and internal_sheet_name == sheet_name_to_save:
                        self._apply_formatting(
                            writer, sheet_name_to_save, df_para_salvar
                        )

            print(f"Planilha salva com sucesso em {self.file_path}")

        except Exception as e:
            print(f"ERRO CRÍTICO ao salvar a planilha: {e}")

    def _apply_formatting(
        self, writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame
    ) -> None:
        # ... (seu método _apply_formatting original - permanece igual) ...
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        header_format = workbook.add_format(
            {"bold": True, "text_wrap": True, "valign": "top", "border": 1}
        )
        currency_format = workbook.add_format({"num_format": "R$ #,##0.00"})
        percentage_format = workbook.add_format({"num_format": "0.0%"})

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            if value in [
                ColunasTransacoes.VALOR,
                ColunasOrcamentos.LIMITE,
                ColunasOrcamentos.GASTO,
                ColunasDividas.VALOR_ORIGINAL,
                ColunasDividas.SALDO_DEVEDOR,
                ColunasDividas.VALOR_PARCELA,
                ColunasMetas.VALOR_ALVO,
                ColunasMetas.VALOR_ATUAL,
            ]:
                worksheet.set_column(col_num, col_num, 15, currency_format)
            elif value == ColunasOrcamentos.PERCENTUAL:
                worksheet.set_column(col_num, col_num, 15, percentage_format)
            else:
                worksheet.set_column(col_num, col_num, 15)
