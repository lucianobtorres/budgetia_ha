# Em: src/finance/services/transaction_service.py

import pandas as pd

from config import ColunasTransacoes, SummaryKeys, ValoresTipo


class TransactionService:
    """
    Classe especialista em realizar cálculos puros de Transações.
    Não possui estado.
    """

    def get_summary(self, df_transacoes: pd.DataFrame) -> dict[str, float]:
        """
        Calcula os totais de receitas, despesas e o saldo
        a partir de um DataFrame de transações.
        """
        df = df_transacoes.copy()

        if df.empty:
            return {
                SummaryKeys.RECEITAS: 0.0,
                SummaryKeys.DESPESAS: 0.0,
                SummaryKeys.SALDO: 0.0,
            }

        if ColunasTransacoes.VALOR not in df.columns:
            return {
                SummaryKeys.RECEITAS: 0.0,
                SummaryKeys.DESPESAS: 0.0,
                SummaryKeys.SALDO: 0.0,
            }
        df[ColunasTransacoes.VALOR] = pd.to_numeric(
            df[ColunasTransacoes.VALOR], errors="coerce"
        ).fillna(0)

        if ColunasTransacoes.TIPO not in df.columns:
            print("AVISO (Trans. Service): DataFrame de transações sem coluna 'Tipo'.")
            return {
                SummaryKeys.RECEITAS: 0.0,
                SummaryKeys.DESPESAS: 0.0,
                SummaryKeys.SALDO: 0.0,
            }

        df_receitas = df[
            df[ColunasTransacoes.TIPO].astype(str).str.lower()
            == ValoresTipo.RECEITA.lower()
        ]
        df_despesas = df[
            df[ColunasTransacoes.TIPO].astype(str).str.lower()
            == ValoresTipo.DESPESA.lower()
        ]

        total_receitas = float(df_receitas[ColunasTransacoes.VALOR].sum())
        total_despesas = float(df_despesas[ColunasTransacoes.VALOR].sum())
        saldo = total_receitas - total_despesas

        return {
            SummaryKeys.RECEITAS: total_receitas,
            SummaryKeys.DESPESAS: total_despesas,
            SummaryKeys.SALDO: saldo,
        }

    def get_expenses_by_category(
        self, df_transacoes: pd.DataFrame, top_n: int = 5
    ) -> pd.Series:
        """
        Retorna as top N categorias por despesa.
        (Movido do FinancialCalculator)
        """
        if (
            df_transacoes.empty
            or ColunasTransacoes.TIPO not in df_transacoes.columns
            or ColunasTransacoes.VALOR not in df_transacoes.columns
        ):
            return pd.Series(dtype=float)

        df = df_transacoes.copy()
        df[ColunasTransacoes.VALOR] = pd.to_numeric(
            df[ColunasTransacoes.VALOR], errors="coerce"
        ).fillna(0)
        df_despesas = df[
            df[ColunasTransacoes.TIPO].astype(str).str.lower()
            == ValoresTipo.DESPESA.lower()
        ]

        if df_despesas.empty:
            return pd.Series(dtype=float)

        series: pd.Series = (
            df_despesas.groupby(ColunasTransacoes.CATEGORIA)[ColunasTransacoes.VALOR]
            .sum()
            .nlargest(top_n)
            .sort_values(ascending=False)
        )
        return series
