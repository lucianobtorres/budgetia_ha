# src/finance/financial_calculator.py

import datetime
from typing import (
    Any,
)

import pandas as pd


class FinancialCalculator:
    """
    Uma classe especialista em realizar todos os cálculos financeiros
    com base nos DataFrames de dados. Não tem estado próprio.
    """

    def calcular_status_orcamentos(
        self, df_transacoes: pd.DataFrame, df_orcamentos: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Recebe os dataframes de transações e orçamentos, calcula os gastos
        atuais e retorna um NOVO dataframe de orçamentos atualizado.
        """
        if df_orcamentos.empty:
            return df_orcamentos  # Retorna o mesmo se não houver o que calcular

        orcamentos_atualizados = df_orcamentos.copy()

        # Prepara um dataframe de despesas do mês/ano corrente para consulta rápida
        df_despesas = self._preparar_despesas_atuais(df_transacoes)

        for index, row in orcamentos_atualizados.iterrows():
            categoria = str(row.get("Categoria", "")).lower()
            limite = row.get("Valor Limite Mensal", 0.0)
            periodo = str(row.get("Período Orçamento", "mensal")).lower()

            gasto_atual = self._calcular_gasto_para_categoria(
                df_despesas, categoria, periodo
            )

            porcentagem = (gasto_atual / limite * 100) if limite > 0 else 0.0

            status = "Ativo"
            if porcentagem >= 100:
                status = "Excedido"
            elif porcentagem >= 80:
                status = "Atenção: Próximo do Limite"

            orcamentos_atualizados.loc[index, "Valor Gasto Atual"] = gasto_atual  # type: ignore[index]
            orcamentos_atualizados.loc[index, "Porcentagem Gasta (%)"] = porcentagem  # type: ignore[index]
            orcamentos_atualizados.loc[index, "Status Orçamento"] = status  # type: ignore[index]
            orcamentos_atualizados.loc[index, "Última Atualização Orçamento"] = (  # type: ignore[index]
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        return orcamentos_atualizados

    def _preparar_despesas_atuais(self, df_transacoes: pd.DataFrame) -> pd.DataFrame:
        """Filtra e prepara apenas as despesas do período relevante."""
        if df_transacoes.empty:
            return pd.DataFrame()

        despesas = df_transacoes[
            df_transacoes["Tipo (Receita/Despesa)"] == "Despesa"
        ].copy()
        if despesas.empty:
            return pd.DataFrame()

        despesas["Data"] = pd.to_datetime(despesas["Data"], errors="coerce")
        despesas["AnoMes"] = despesas["Data"].dt.to_period("M")
        return despesas

    def _calcular_gasto_para_categoria(
        self, df_despesas: pd.DataFrame, categoria: str, periodo: str
    ) -> float:
        """Calcula o gasto total para uma categoria e período."""
        if df_despesas.empty:
            return 0.0

        if periodo == "mensal":
            mes_corrente = pd.Period(datetime.datetime.now(), freq="M")
            gastos_df = df_despesas[
                (df_despesas["Categoria"].astype(str).str.lower() == categoria)
                & (df_despesas["AnoMes"] == mes_corrente)
            ]
            return float(gastos_df["Valor"].sum())

        # Adicionar lógica para 'anual' se necessário
        return 0.0

    def get_summary(self, df_transacoes: pd.DataFrame) -> dict[str, float]:
        """Calcula e retorna totais de receitas, despesas e saldo."""
        if df_transacoes.empty:
            return {"receitas": 0.0, "despesas": 0.0, "saldo": 0.0}

        total_receitas = df_transacoes[
            df_transacoes["Tipo (Receita/Despesa)"] == "Receita"
        ]["Valor"].sum()
        total_despesas = df_transacoes[
            df_transacoes["Tipo (Receita/Despesa)"] == "Despesa"
        ]["Valor"].sum()
        saldo_atual = total_receitas - total_despesas

        return {
            "receitas": total_receitas,
            "despesas": total_despesas,
            "saldo": saldo_atual,
        }

    def get_expenses_by_category(
        self, df_transacoes: pd.DataFrame, top_n: int = 5
    ) -> pd.Series:
        """Calcula e retorna as 'N' maiores categorias de despesa."""
        if df_transacoes.empty:
            return pd.Series(dtype=float)

        return (
            df_transacoes[df_transacoes["Tipo (Receita/Despesa)"] == "Despesa"]
            .groupby("Categoria")["Valor"]
            .sum()
            .nlargest(top_n)
        )

    def calcular_saldo_devedor(
        self,
        valor_parcela: float,
        taxa_juros_mensal: float,
        parcelas_totais: int,
        parcelas_pagas: int,
    ) -> float:
        """Calcula o valor presente (saldo devedor) de uma dívida."""
        juros = taxa_juros_mensal / 100
        parcelas_restantes = parcelas_totais - parcelas_pagas

        if parcelas_restantes <= 0:
            return 0.0

        if juros > 0:
            # Fórmula do Valor Presente de uma anuidade
            return valor_parcela * (1 - (1 + juros) ** -parcelas_restantes) / juros
        else:
            # Se não há juros, é simplesmente o valor das parcelas restantes
            return valor_parcela * parcelas_restantes

    def gerar_analise_proativa(
        self, df_orcamentos: pd.DataFrame, saldo_total: float
    ) -> list[dict[str, Any]]:
        """
        Analisa os orçamentos e o saldo, retornando uma lista de insights acionáveis.
        """
        insights_gerados = []

        # 1. Análise de Orçamentos
        if not df_orcamentos.empty:
            for _, row in df_orcamentos.iterrows():
                # Garantir que os valores são numéricos antes de comparar
                try:
                    status = str(row.get("Status Orçamento", "")).strip()
                    categoria = str(row.get("Categoria", "N/A"))
                    gasto_atual = float(row.get("Valor Gasto Atual", 0.0))
                    limite = float(row.get("Valor Limite Mensal", 0.0))
                    porcentagem = float(row.get("Porcentagem Gasta (%)", 0.0))
                except ValueError:
                    continue  # Pula linha com dados inválidos

                if status == "Excedido":
                    insights_gerados.append(
                        {
                            "tipo_insight": "Alerta de Orçamento Excedido",
                            "titulo_insight": f"Atenção: Orçamento de '{categoria}' excedido!",
                            "detalhes_recomendacao": (
                                f"Você gastou R$ {gasto_atual:,.2f} em '{categoria}', "
                                f"excedendo o limite de R$ {limite:,.2f}. "
                                "É importante revisar seus gastos nesta categoria."
                            ),
                        }
                    )
                elif status == "Atenção: Próximo do Limite":
                    insights_gerados.append(
                        {
                            "tipo_insight": "Atenção ao Orçamento",
                            "titulo_insight": f"Alerta: Orçamento de '{categoria}' próximo do limite.",
                            "detalhes_recomendacao": (
                                f"Você já usou {porcentagem:.1f}% do seu orçamento de '{categoria}'. "
                                f"O gasto atual é de R$ {gasto_atual:,.2f} do total de "
                                f"R$ {limite:,.2f}. "
                                "Mantenha o controle!"
                            ),
                        }
                    )

        # 2. Análise de Saldo Total
        if saldo_total < 0:
            insights_gerados.append(
                {
                    "tipo_insight": "Alerta de Saldo Negativo",
                    "titulo_insight": "Seu balanço geral está negativo.",
                    "detalhes_recomendacao": (
                        f"Atualmente, seu balanço total é de R$ {saldo_total:,.2f}. "
                        "Isso indica que suas despesas estão superando suas receitas. "
                        "Vamos analisar seus gastos para encontrar economias."
                    ),
                }
            )
        elif saldo_total > 0:
            insights_gerados.append(
                {
                    "tipo_insight": "Sugestão de Economia",
                    "titulo_insight": "Ótimo! Seu saldo está positivo.",
                    "detalhes_recomendacao": (
                        f"Seu balanço atual é de R$ {saldo_total:,.2f}. "
                        "Este é um excelente momento para pensar em sua reserva de emergência "
                        "ou em uma meta de investimento."
                    ),
                }
            )

        return insights_gerados

    def calcular_saldo_devedor_atual(
        self,
        valor_parcela: float,
        taxa_juros_mensal: float,
        parcelas_totais: int,
        parcelas_pagas: int,
    ) -> float:
        """
        Calcula o saldo devedor atual (Valor Presente) de um financiamento.
        """
        juros = taxa_juros_mensal / 100
        parcelas_restantes = parcelas_totais - parcelas_pagas

        if parcelas_restantes <= 0:
            return 0.0

        if juros > 0:
            # Fórmula do Valor Presente de uma anuidade
            saldo_devedor = (
                valor_parcela * (1 - (1 + juros) ** (-parcelas_restantes)) / juros
            )
        else:
            # Se não há juros, é só multiplicar
            saldo_devedor = valor_parcela * parcelas_restantes

        return float(saldo_devedor)
