# Em: src/finance/mapping_strategies/custom_json_strategy.py

from typing import Any

import pandas as pd

import config

from .base_strategy import BaseMappingStrategy


class CustomJsonStrategy(BaseMappingStrategy):
    """
    Estratégia que usa o dicionário 'mapeamento' (do user_config.json)
    para renomear colunas e aplicar transformações.
    """

    def __init__(
        self, layout_config: dict[str, Any], mapeamento: dict[str, Any] | None = None
    ):
        super().__init__(layout_config, mapeamento)
        print("LOG: Estratégia 'CustomJsonStrategy' selecionada.")

        # Pre-calcula o mapa reverso para salvar
        mapa_colunas_direto = self.mapeamento.get("colunas", {})
        self.mapa_reverso = {v: k for k, v in mapa_colunas_direto.items()}
        self.colunas_originais_usuario = list(mapa_colunas_direto.keys())

    def map_transactions(self, df_bruto: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica a lógica de LEITURA: (Planilha do Usuário) -> (Nosso Formato)
        """
        df_mapeado = df_bruto.copy()

        # 1. Renomear colunas (SuaColuna -> NossaColuna)
        mapa_colunas = self.mapeamento.get("colunas", {})
        if mapa_colunas:
            print(f"LOG: Aplicando renomeação de colunas: {mapa_colunas}")
            df_mapeado.rename(columns=mapa_colunas, inplace=True)

        # 2. Aplicar transformações (Ex: Valores Negativos)
        if self.mapeamento.get("transform_valor_negativo", False):
            print("LOG: Aplicando transformação de valor negativo...")
            if "Valor" in df_mapeado.columns:
                df_mapeado["Tipo (Receita/Despesa)"] = df_mapeado["Valor"].apply(
                    lambda x: "Receita" if pd.notna(x) and x > 0 else "Despesa"
                )
                df_mapeado["Valor"] = df_mapeado["Valor"].abs()
            else:
                print(
                    "AVISO: 'transform_valor_negativo' ligado, mas 'Valor' não encontrado."
                )

        # 3. Garantir todas as colunas padrão (lógica da classe base)
        # Isso garante que colunas como 'ID Transacao', 'Status', etc., existam
        df_final = self.map_other_sheet(df_mapeado, config.NomesAbas.TRANSACOES)

        return df_final

    def unmap_transactions(self, df_interno: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica a lógica de ESCRITA: (Nosso Formato) -> (Planilha do Usuário)
        """
        df_para_salvar = df_interno.copy()

        # 1. Aplicar transformação de valor negativo (operação inversa)
        if self.mapeamento.get("transform_valor_negativo", False):
            print("LOG: Aplicando transformação INVERSA de valor negativo...")
            if (
                "Valor" in df_para_salvar.columns
                and "Tipo (Receita/Despesa)" in df_para_salvar.columns
            ):
                df_para_salvar["Valor"] = df_para_salvar.apply(
                    lambda row: row["Valor"] * -1
                    if row["Tipo (Receita/Despesa)"] == "Despesa"
                    else row["Valor"],
                    axis=1,
                )

                # Se a coluna "Tipo" não foi mapeada pelo usuário, removemos
                if "Tipo (Receita/Despesa)" not in self.mapa_reverso:
                    df_para_salvar = df_para_salvar.drop(
                        columns=["Tipo (Receita/Despesa)"]
                    )

        # 2. Renomear colunas (operação inversa: NossaColuna -> SuaColuna)
        if self.mapa_reverso:
            print(f"LOG: Aplicando renomeação INVERSA: {self.mapa_reverso}")
            df_para_salvar.rename(columns=self.mapa_reverso, inplace=True)

        # 3. Manter APENAS as colunas originais do usuário
        # Isso remove colunas internas (ID Transacao, Status) que nós criamos
        colunas_finais = [
            col
            for col in df_para_salvar.columns
            if col in self.colunas_originais_usuario
        ]

        if not colunas_finais:
            # Segurança: Se o mapa estiver vazio, não quebra
            print(
                "AVISO: Mapa de colunas reverso está vazio. Salvando colunas internas."
            )
            return df_interno[self.colunas_transacoes]  # Salva o padrão

        print(f"LOG: Salvando apenas colunas originais do usuário: {colunas_finais}")
        # Retorna o DataFrame apenas com as colunas do usuário, na ordem que ele mapeou
        return df_para_salvar[self.colunas_originais_usuario]
