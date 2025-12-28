# Em: src/finance/strategies/default_strategy.py

from typing import Any

import pandas as pd

import config

from .base_strategy import BaseMappingStrategy


class DefaultStrategy(BaseMappingStrategy):
    """
    Estratégia para o layout padrão. Assume que as abas e colunas
    já correspondem ao layout do sistema (ou serão criadas).
    """

    def __init__(
        self, layout_config: dict[str, Any], mapeamento: dict[str, Any] | None = None
    ):
        super().__init__(layout_config, mapeamento)
        print("LOG: Estratégia 'DefaultStrategy' selecionada.")

    def map_transactions(self, df_bruto: pd.DataFrame) -> pd.DataFrame:
        """
        Para a estratégia padrão, apenas garantimos que as colunas
        do nosso layout de transações existam.
        """
        # --- INÍCIO DA CORREÇÃO ---
        # Garante a conversão de tipo para a coluna de Data
        coluna_data_padrao = "Data"  # Nome padrão da coluna no nosso sistema

        if coluna_data_padrao in df_bruto.columns:
            try:
                print(
                    f"--- DEBUG (DefaultStrategy): Convertendo coluna '{coluna_data_padrao}' para datetime... ---"
                )
                df_bruto[coluna_data_padrao] = pd.to_datetime(
                    df_bruto[coluna_data_padrao], errors="coerce"
                )
                print(
                    f"--- DEBUG (DefaultStrategy): Conversão concluída. Valores nulos após conversão: {df_bruto[coluna_data_padrao].isna().sum()} ---"
                )
            except Exception as e:
                print(
                    f"AVISO (DefaultStrategy): Falha ao converter coluna '{coluna_data_padrao}' para datetime: {e}"
                )
                # Se falhar, continua, mas o data_editor pode quebrar
        # --- FIM DA CORREÇÃO ---

        # Reutiliza a lógica genérica da classe base para garantir as colunas
        return self.map_other_sheet(df_bruto, config.NomesAbas.TRANSACOES)

    def unmap_transactions(self, df_interno: pd.DataFrame) -> pd.DataFrame:
        """
        Na estratégia padrão, o formato interno JÁ É o formato do usuário.
        Apenas retornamos o DataFrame como está.
        """
        # (Opcional: podemos remover colunas internas como 'ID Transacao' se quisermos)
        colunas_para_salvar = [
            col for col in df_interno.columns if col in self.colunas_transacoes
        ]

        # Retorna apenas as colunas definidas no layout, na ordem correta
        return df_interno[colunas_para_salvar]
