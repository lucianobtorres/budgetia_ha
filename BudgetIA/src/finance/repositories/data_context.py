# src/finance/repositories/data_context.py
from typing import Any

import pandas as pd

import config

# Import relativo para "subir" um nível
from ..excel_handler import ExcelHandler


class FinancialDataContext:
    """
    Unidade de Trabalho (Unit of Work).
    Responsabilidade Única: Gerenciar o estado dos DataFrames em memória (self.dfs)
    e coordenar a persistência (leitura/escrita) através do ExcelHandler.
    """

    def __init__(
        self,
        excel_handler: ExcelHandler,
        mapeamento: dict[str, Any] | None = None,
    ) -> None:
        """
        Inicializa o contexto, carregando os dados da planilha para a memória.
        """
        self.excel_handler = excel_handler
        self.dfs, self.is_new_file = self.excel_handler.load_sheets(
            config.LAYOUT_PLANILHA, mapeamento
        )
        print("LOG: FinancialDataContext inicializado.")

    def get_dataframe(self, aba_nome: str) -> pd.DataFrame:
        """
        Retorna uma CÓPIA do DataFrame solicitado para leitura/análise segura.
        Cria um DataFrame vazio em memória se a aba for conhecida mas não existir.
        """
        if aba_nome not in self.dfs:
            if aba_nome in config.LAYOUT_PLANILHA:
                print(
                    f"AVISO: Tentando acessar aba '{aba_nome}' que não foi carregada. Criando em memória."
                )
                self.dfs[aba_nome] = pd.DataFrame(
                    columns=config.LAYOUT_PLANILHA[aba_nome]
                )
            else:
                print(f"ERRO: Tentando acessar aba desconhecida '{aba_nome}'.")
                return pd.DataFrame()

        # Retorna uma cópia para evitar mutações inesperadas do estado
        return self.dfs.get(aba_nome, pd.DataFrame()).copy()

    def update_dataframe(self, aba_nome: str, new_df: pd.DataFrame) -> None:
        """
        Atualiza um DataFrame inteiro na memória (na Unidade de Trabalho).
        As mudanças só serão persistidas quando .save() for chamado.
        """
        if aba_nome in self.dfs:
            # Garante que as colunas e ordem estejam corretas
            if aba_nome in config.LAYOUT_PLANILHA:
                colunas_layout = config.LAYOUT_PLANILHA[aba_nome]
                # Adiciona colunas do layout que estão faltando no new_df
                for col in colunas_layout:
                    if col not in new_df.columns:
                        new_df[col] = pd.NA
                # Reordena e filtra para bater exatamente com o layout
                try:
                    new_df = new_df[colunas_layout]
                except KeyError as e:
                    print(
                        f"ERRO: Colunas do DataFrame '{aba_nome}' não batem com o LAYOUT. {e}"
                    )
                    # Não atualiza se as colunas estiverem erradas
                    return

            self.dfs[aba_nome] = new_df
        else:
            print(
                f"ERRO: Tentativa de atualizar aba '{aba_nome}' que não existe no self.dfs."
            )

    def save(self, add_intelligence: bool = False) -> None:
        """
        Persiste TODOS os DataFrames da memória de volta ao arquivo Excel.
        """
        print(
            f"LOG: Solicitando salvamento ao ExcelHandler para '{self.excel_handler.file_path}'"
        )
        # Passa o 'self.dfs' para o handler salvar
        self.excel_handler.save_sheets(self.dfs, add_intelligence)
