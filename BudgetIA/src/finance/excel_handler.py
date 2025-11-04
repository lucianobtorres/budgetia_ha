# Em: src/finance/excel_handler.py
import os
from typing import Any  # Importações atualizadas

import pandas as pd

import config  # Importar config para NomesAbas


class ExcelHandler:
    """Classe especialista em ler e escrever DataFrames para um arquivo Excel."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        # A flag is_new_file será determinada pelo load_sheets
        self.is_new_file = not os.path.exists(self.file_path)

    def load_sheets(
        self,
        layout_config: dict[str, list[str]],  # Renomeado 'schema' para 'layout_config'
        mapeamento: dict[str, Any] | None = None,  # <-- NOVO ARGUMENTO
    ) -> tuple[dict[str, pd.DataFrame], bool]:
        """
        Carrega as abas da planilha.
        Se 'mapeamento' for None, usa o 'layout_config' padrão.
        Se 'mapeamento' for fornecido, usa a lógica de mapeamento (Strategy Pattern).
        Retorna os DataFrames e um booleano 'is_new_file'.
        """
        dataframes: dict[str, pd.DataFrame] = {}
        is_new_file = self.is_new_file  # Pega o estado inicial

        # --- NOVA LÓGICA DE MAPEAMENTO (Strategy Pattern) ---
        if mapeamento:
            print(
                f"LOG: Mapeamento de usuário detectado. Aplicando estratégia '{mapeamento.get('strategy_module', 'custom')}'..."
            )

            # (No futuro, aqui carregaria dinamicamente a estratégia)
            # (Por agora, simulamos uma leitura mapeada simples)

            try:
                # 1. Carregar aba de transações mapeada
                aba_usuario_transacoes = mapeamento.get(
                    "aba_transacoes", config.NomesAbas.TRANSACOES
                )

                # TODO: Implementar lógica de estratégia real (ex: pd.concat para múltiplas abas)
                df_transacoes = pd.read_excel(
                    self.file_path, sheet_name=aba_usuario_transacoes
                )

                # 2. Renomear colunas
                mapa_colunas = mapeamento.get("colunas", {})
                df_transacoes.rename(columns=mapa_colunas, inplace=True)

                # 3. Aplicar transformações (Ex: Valores Negativos)
                if mapeamento.get("transform_valor_negativo", False):
                    if "Valor" in df_transacoes.columns:
                        df_transacoes["Tipo (Receita/Despesa)"] = df_transacoes[
                            "Valor"
                        ].apply(lambda x: "Receita" if x > 0 else "Despesa")
                        df_transacoes["Valor"] = df_transacoes["Valor"].abs()

                # Salva o DF traduzido em nossa chave interna padrão
                dataframes[config.NomesAbas.TRANSACOES] = df_transacoes
                print(
                    f"LOG: Aba '{aba_usuario_transacoes}' carregada e mapeada para '{config.NomesAbas.TRANSACOES}'."
                )

            except FileNotFoundError:
                print(
                    f"ERRO: Arquivo '{self.file_path}' não encontrado durante o mapeamento."
                )
                is_new_file = True
                dataframes[config.NomesAbas.TRANSACOES] = pd.DataFrame(
                    columns=layout_config[config.NomesAbas.TRANSACOES]
                )
            except Exception as e:
                print(
                    f"ERRO ao carregar aba mapeada '{aba_usuario_transacoes}': {e}. Criando aba vazia."
                )
                is_new_file = True
                dataframes[config.NomesAbas.TRANSACOES] = pd.DataFrame(
                    columns=layout_config[config.NomesAbas.TRANSACOES]
                )

            # 4. Carregar as *outras* abas (Orçamentos, Dívidas, Perfil)
            #    (Assumimos que elas *devem* existir ou serão criadas por nós)
            for aba_nome, colunas in layout_config.items():
                if (
                    aba_nome not in dataframes
                ):  # Se ainda não foi carregada (ex: TRANSACOES já foi)
                    try:
                        dataframes[aba_nome] = pd.read_excel(
                            self.file_path, sheet_name=aba_nome
                        )
                        # Garantir que as colunas esperadas existam
                        for col in colunas:
                            if col not in dataframes[aba_nome].columns:
                                dataframes[aba_nome][col] = pd.NA
                    except Exception:
                        print(
                            f"AVISO: Aba '{aba_nome}' (padrão do sistema) não encontrada. Criando vazia."
                        )
                        dataframes[aba_nome] = pd.DataFrame(columns=colunas)
                        is_new_file = (
                            True  # Se abas do sistema faltam, precisamos salvar
                        )

        # --- LÓGICA PADRÃO (O que tínhamos antes, agora no 'else') ---
        else:
            print("LOG: Nenhum mapeamento detectado. Carregando layout padrão...")
            if is_new_file:
                print(
                    f"AVISO: Arquivo '{self.file_path}' não encontrado. Estrutura criada em memória."
                )
                for sheet_name, columns in layout_config.items():
                    dataframes[sheet_name] = pd.DataFrame(columns=columns)
            else:
                print(f"LOG: Carregando planilha existente de '{self.file_path}'.")
                try:
                    xls = pd.ExcelFile(self.file_path)
                    abas_existentes = xls.sheet_names

                    for sheet_name, columns in layout_config.items():
                        if sheet_name in abas_existentes:
                            dataframes[sheet_name] = pd.read_excel(
                                xls, sheet_name=sheet_name
                            )
                            # Garantir colunas (para planilhas antigas)
                            for col in columns:
                                if col not in dataframes[sheet_name].columns:
                                    dataframes[sheet_name][col] = pd.NA
                        else:
                            print(
                                f"AVISO: Aba '{sheet_name}' não encontrada no arquivo. Criando aba vazia."
                            )
                            is_new_file = (
                                True  # Se *qualquer* aba faltar, é novo/incompleto
                            )
                            dataframes[sheet_name] = pd.DataFrame(columns=columns)
                except Exception as e:
                    print(
                        f"ERRO CRÍTICO ao ler o arquivo Excel: {e}. Criando estrutura do zero em memória."
                    )
                    is_new_file = True  # Trata como novo se a leitura falhar
                    for sheet_name, columns in layout_config.items():
                        dataframes[sheet_name] = pd.DataFrame(columns=columns)

        self.is_new_file = is_new_file  # Armazena o estado final
        return dataframes, is_new_file

    def save_sheets(
        self, dataframes: dict[str, pd.DataFrame], add_intelligence: bool = False
    ) -> None:
        """Salva um dicionário de DataFrames em um arquivo Excel com abas."""
        # NOTA: Esta função ainda salva com a NOSSA estrutura.
        # A "tradução inversa" para planilhas mapeadas não está implementada (Fase 3).
        try:
            with pd.ExcelWriter(self.file_path, engine="xlsxwriter") as writer:
                for sheet_name, df in dataframes.items():
                    # Tratar NaT (Not a Time) antes de salvar, que xlsxwriter não suporta
                    for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
                        df[col] = df[col].astype(object).where(df[col].notna(), None)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    if add_intelligence:
                        self._apply_formatting(writer, sheet_name, df)
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
                "Valor",
                "Valor Limite Mensal",
                "Valor Gasto Atual",
                "Valor Original",
                "Saldo Devedor Atual",
                "Valor Parcela",
                "Valor Alvo",
                "Valor Atual",
            ]:
                worksheet.set_column(col_num, col_num, 15, currency_format)
            elif value == "Porcentagem Gasta (%)":
                worksheet.set_column(col_num, col_num, 15, percentage_format)
            else:
                worksheet.set_column(col_num, col_num, 15)
