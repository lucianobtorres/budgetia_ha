# Em: src/finance/financial_calculator.py
import datetime
from typing import Any

import numpy_financial as npf
import pandas as pd

from config import ColunasOrcamentos, ColunasTransacoes, SummaryKeys, ValoresTipo

# Removido o import desnecessário de 'npv'
# from numpy_financial import npv


class FinancialCalculator:
    """
    Classe especialista em realizar cálculos financeiros puros.
    Não possui estado e não conhece a planilha.
    """

    def get_summary(self, df_transacoes: pd.DataFrame) -> dict[str, float]:
        """
        Calcula os totais de receitas, despesas e o saldo
        a partir de um DataFrame de transações.
        """
        df = df_transacoes.copy()

        # O teste 'test_get_summary_dataframe_vazio' passa um DF vazio
        if df.empty:
            return {
                SummaryKeys.RECEITAS: 0.0,
                SummaryKeys.DESPESAS: 0.0,
                SummaryKeys.SALDO: 0.0,
            }

        # Garante que 'Valor' é numérico
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
            print("AVISO (Calculator): DataFrame de transações sem coluna 'Tipo'.")
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

    def calcular_saldo_devedor_atual(
        self,
        valor_parcela: float,
        taxa_juros_mensal: float,
        parcelas_totais: int,
        parcelas_pagas: int,
    ) -> float:
        """
        Calcula o Saldo Devedor Atual (PV) de um financiamento.
        """
        if taxa_juros_mensal <= 0:
            return float(valor_parcela * (parcelas_totais - parcelas_pagas))

        taxa_decimal = taxa_juros_mensal / 100.0
        parcelas_restantes = parcelas_totais - parcelas_pagas

        if parcelas_restantes <= 0:
            return 0.0

        try:
            saldo_devedor = npf.pv(
                rate=taxa_decimal,
                nper=parcelas_restantes,
                pmt=-valor_parcela,
                when="end",
            )
            return float(saldo_devedor)
        except Exception as e:
            print(f"Erro ao calcular PV: {e}")
            return float(valor_parcela * parcelas_restantes)

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
            "Valor"
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
                lambda row: "Estourado"
                if row[ColunasOrcamentos.PERCENTUAL] > 100
                else ("Alerta" if row[ColunasOrcamentos.PERCENTUAL] > 90 else "OK"),
                axis=1,
            )
        )

        df_orc_atualizado["Última Atualização Orçamento"] = (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        return df_orc_atualizado

    def get_expenses_by_category(
        self, df_transacoes: pd.DataFrame, top_n: int = 5
    ) -> pd.Series:
        """Retorna as top N categorias por despesa."""
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

        return (
            df_despesas.groupby(ColunasTransacoes.CATEGORIA)[ColunasTransacoes.VALOR]
            .sum()
            .nlargest(top_n)
            .sort_values(ascending=False)
        )

    def gerar_analise_proativa(
        self, orcamentos_df: pd.DataFrame, saldo_total: float
    ) -> list[dict[str, Any]]:
        """Gera insights proativos com base no status do orçamento."""
        insights = []
        if orcamentos_df.empty or ColunasOrcamentos.STATUS not in orcamentos_df.columns:
            return insights

        # --- CORREÇÃO (Falha 4) ---
        # Procura por "Estourado" (que é o que 'calcular_status_orcamentos' gera)
        orcamentos_estourados = orcamentos_df[
            orcamentos_df[ColunasOrcamentos.STATUS] == "Estourado"
        ]
        for _, row in orcamentos_estourados.iterrows():
            insights.append(
                {
                    "tipo_insight": "Alerta de Orçamento",
                    "titulo_insight": f"Orçamento Estourado: {row[ColunasOrcamentos.CATEGORIA]}",
                    "detalhes_recomendacao": f"Você ultrapassou o limite de R$ {row[ColunasOrcamentos.LIMITE]:,.2f} para {row[ColunasOrcamentos.CATEGORIA]}, gastando R$ {row[ColunasOrcamentos.GASTO]:,.2f}. Recomendo revisar seus gastos nesta categoria.",
                }
            )

        # --- CORREÇÃO (Falha 4) ---
        # Procura por "Alerta"
        orcamentos_alerta = orcamentos_df[
            orcamentos_df[ColunasOrcamentos.STATUS] == "Alerta"
        ]
        for _, row in orcamentos_alerta.iterrows():
            insights.append(
                {
                    "tipo_insight": "Aviso de Orçamento",
                    "titulo_insight": f"Orçamento em Alerta: {row[ColunasOrcamentos.CATEGORIA]}",
                    "detalhes_recomendacao": f"Você está próximo do limite de R$ {row[ColunasOrcamentos.LIMITE]:,.2f} para {row[ColunasOrcamentos.CATEGORIA]}, já gastou R$ {row[ColunasOrcamentos.GASTO]:,.2f} ({row[ColunasOrcamentos.PERCENTUAL]:.1f}%). Atenção aos próximos gastos.",
                }
            )
        # --- FIM DA CORREÇÃO ---

        if saldo_total < 0:
            insights.append(
                {
                    "tipo_insight": "Alerta de Saldo",
                    "titulo_insight": "Saldo Negativo",
                    "detalhes_recomendacao": f"Seu saldo total está negativo em R$ {saldo_total:,.2f}. É crucial revisar suas receitas e despesas para evitar dívidas.",
                }
            )

        # --- CORREÇÃO (Falha 5) ---
        # Adiciona insight "saudável" se não houver alertas
        if not insights and saldo_total > 0:
            insights.append(
                {
                    "tipo_insight": "Sugestão de Economia",
                    "titulo_insight": "Parabéns pelo Saldo Positivo!",
                    "detalhes_recomendacao": f"Seu saldo este mês está positivo em R$ {saldo_total:,.2f} e seus orçamentos estão sob controle. Considere investir ou poupar parte desse valor.",
                }
            )
        # --- FIM DA CORREÇÃO ---

        return insights
