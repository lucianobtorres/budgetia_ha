# Em: src/finance/services/budget_service.py

import datetime

import pandas as pd

from config import ColunasOrcamentos, ColunasTransacoes, ValoresTipo


class BudgetService:
    """
    Classe especialista em realizar cálculos puros de Orçamentos.
    Não possui estado.
    """

    def calcular_status_orcamentos(
        self, df_transacoes: pd.DataFrame, df_orcamentos: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calcula o gasto atual para cada orçamento com base nas transações.
        """
        if df_orcamentos.empty:
            return df_orcamentos

        df_orc_atualizado = df_orcamentos.copy()

        # Garante colunas de status mesmo se não houver transações
        if ColunasOrcamentos.GASTO not in df_orc_atualizado.columns:
            df_orc_atualizado[ColunasOrcamentos.GASTO] = 0.0
        if ColunasOrcamentos.PERCENTUAL not in df_orc_atualizado.columns:
            df_orc_atualizado[ColunasOrcamentos.PERCENTUAL] = 0.0
        if ColunasOrcamentos.STATUS not in df_orc_atualizado.columns:
            df_orc_atualizado[ColunasOrcamentos.STATUS] = "OK"

        if df_transacoes.empty:
            df_orc_atualizado[ColunasOrcamentos.GASTO] = 0.0
            df_orc_atualizado[ColunasOrcamentos.PERCENTUAL] = 0.0
            df_orc_atualizado[ColunasOrcamentos.STATUS] = "OK"
            return df_orc_atualizado

        if (
            ColunasTransacoes.VALOR not in df_transacoes.columns
            or ColunasTransacoes.CATEGORIA not in df_transacoes.columns
        ):
            return df_orc_atualizado

        df_transacoes[ColunasTransacoes.VALOR] = pd.to_numeric(
            df_transacoes[ColunasTransacoes.VALOR], errors="coerce"
        ).fillna(0)
        df_despesas = df_transacoes[
            df_transacoes[ColunasTransacoes.TIPO].astype(str).str.lower()
            == ValoresTipo.DESPESA.lower()
        ].copy()

        # --- Lógica de filtro de data (para Falha 3) ---
        # Garante que 'Data' exista e seja datetime
        if ColunasTransacoes.DATA in df_despesas.columns:
            df_despesas[ColunasTransacoes.DATA] = pd.to_datetime(
                df_despesas[ColunasTransacoes.DATA], errors="coerce"
            )
            df_despesas.dropna(
                subset=[ColunasTransacoes.DATA], inplace=True
            )  # Remove transações sem data válida

            # Filtra para o mês atual
            hoje = datetime.datetime.now()
            df_despesas = df_despesas[
                (df_despesas[ColunasTransacoes.DATA].dt.year == hoje.year)
                & (df_despesas[ColunasTransacoes.DATA].dt.month == hoje.month)
            ]
        else:
            print(
                "AVISO (Calculator): Transações sem coluna 'Data'. Calculando orçamento com todas as transações."
            )
        # --- Fim da lógica de data ---

        gastos_por_categoria = df_despesas.groupby(ColunasTransacoes.CATEGORIA)[
            ColunasTransacoes.VALOR
        ].sum()

        def calcular_gasto(row: pd.Series) -> float:
            categoria = row[ColunasTransacoes.CATEGORIA]
            if categoria in gastos_por_categoria:
                return float(gastos_por_categoria[categoria])
            return 0.0  # Se não houver gasto, retorna 0 (não o valor antigo)

        df_orc_atualizado[ColunasOrcamentos.GASTO] = df_orc_atualizado.apply(
            calcular_gasto, axis=1
        )

        df_orc_atualizado[ColunasOrcamentos.LIMITE] = pd.to_numeric(
            df_orc_atualizado[ColunasOrcamentos.LIMITE], errors="coerce"
        ).fillna(0)

        df_orc_atualizado[ColunasOrcamentos.PERCENTUAL] = 0.0
        # Filtro para evitar divisão por zero
        filtro_limite_valido = df_orc_atualizado[ColunasOrcamentos.LIMITE] > 0

        df_orc_atualizado.loc[filtro_limite_valido, ColunasOrcamentos.PERCENTUAL] = (
            df_orc_atualizado[ColunasOrcamentos.GASTO]
            / df_orc_atualizado[ColunasOrcamentos.LIMITE]
        ) * 100

        # --- CORREÇÃO (NameError - Falha 3) ---
        # Troca 'df_orc_totalizado' por 'df_orc_atualizado'
        conditions = [
            (df_orc_atualizado[ColunasOrcamentos.PERCENTUAL] > 100),
            (df_orc_atualizado[ColunasOrcamentos.PERCENTUAL] > 90),
        ]
        # --- FIM DA CORREÇÃO ---

        choices = ["Estourado", "Alerta"]

        # Define 'OK' como padrão e aplica as condições
        df_orc_atualizado[ColunasOrcamentos.STATUS] = "OK"
        df_orc_atualizado[ColunasOrcamentos.STATUS] = pd.Series(
            df_orc_atualizado.apply(
                lambda row: (
                    "Estourado"
                    if row[ColunasOrcamentos.PERCENTUAL] > 100
                    else ("Alerta" if row[ColunasOrcamentos.PERCENTUAL] > 90 else "OK")
                ),
                axis=1,
            )
        )

        df_orc_atualizado[ColunasOrcamentos.ATUALIZACAO] = datetime.datetime.now()
        return df_orc_atualizado
