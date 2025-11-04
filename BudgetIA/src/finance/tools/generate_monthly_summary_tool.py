import json

import pandas as pd
from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import GerarResumoMensalInput


class GerarResumoMensalTool(BaseTool):  # type: ignore[misc]
    name: str = "gerar_resumo_mensal"
    description: str = (
        "Gera um resumo detalhado de receitas, despesas e saldo para um mês/ano específico "
        "ou para todos os meses disponíveis se nenhum for especificado. "
        "Use esta ferramenta quando o usuário pedir 'Resumo do mês X', 'Balanço de Y', "
        "'Qual meu lucro/prejuízo em março?', 'Me dê um resumo geral'."
    )
    args_schema: type[BaseModel] = GerarResumoMensalInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self, ano: int | None = None, mes: int | None = None) -> str:
        print(f"LOG: Ferramenta '{self.name}' chamada para Ano={ano}, Mês={mes}.")
        df = self.planilha_manager.visualizar_dados(aba_nome="Visão Geral e Transações")
        if df.empty:
            return "Não há dados na planilha para gerar um resumo mensal."

        df["Data"] = pd.to_datetime(df["Data"])
        df["AnoMes"] = df["Data"].dt.to_period("M")

        if ano and mes:
            periodo_filtro = pd.Period(year=ano, month=mes, freq="M")
            df_filtrado = df[df["AnoMes"] == periodo_filtro]
            if df_filtrado.empty:
                return f"Não há transações para o mês {mes}/{ano}."
            resumo_por_periodo = self._calcular_resumo_para_df(df_filtrado)
            return (
                f"Resumo para {mes}/{ano}:\n{json.dumps(resumo_por_periodo, indent=2)}"
            )
        elif ano:
            df_filtrado = df[df["Data"].dt.year == ano]
            if df_filtrado.empty:
                return f"Não há transações para o ano {ano}."

            resumos = {}
            for periodo, grupo in df_filtrado.groupby("AnoMes"):
                resumos[str(periodo)] = self._calcular_resumo_para_df(grupo)

            return f"Resumo para o ano {ano}:\n{json.dumps(resumos, indent=2)}"
        else:  # Resumo geral por mês
            resumos = {}
            for periodo, grupo in df.groupby("AnoMes"):
                resumos[str(periodo)] = self._calcular_resumo_para_df(grupo)

            return f"Resumo geral por mês:\n{json.dumps(resumos, indent=2)}"

    def _calcular_resumo_para_df(self, df_periodo: pd.DataFrame) -> dict[str, float]:
        """Função auxiliar para calcular resumo para um DataFrame de um período."""
        receitas = df_periodo[df_periodo["Tipo (Receita/Despesa)"] == "Receita"][
            "Valor"
        ].sum()
        despesas = df_periodo[df_periodo["Tipo (Receita/Despesa)"] == "Despesa"][
            "Valor"
        ].sum()
        saldo = receitas - despesas
        return {
            "Receitas": float(receitas),
            "Despesas": float(despesas),
            "Saldo": float(saldo),
        }
