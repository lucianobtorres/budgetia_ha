import pandas as pd
from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import AnalisarTendenciasGastosInput


class AnalisarTendenciasGastosTool(BaseTool):  # type: ignore[misc]
    name: str = "analisar_tendencias_gastos"
    description: str = (
        "Analisa e retorna as tendências de gastos ao longo do tempo, opcionalmente por categoria. "
        "Útil para identificar se os gastos estão aumentando ou diminuindo. "
        "Use esta ferramenta quando o usuário perguntar 'Meus gastos de X estão aumentando?', "
        "'Qual a tendência das minhas despesas totais?'."
    )
    args_schema: type[BaseModel] = AnalisarTendenciasGastosInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self, categoria: str | None = None) -> str:
        print(f"LOG: Ferramenta '{self.name}' chamada para Categoria={categoria}.")
        df = self.planilha_manager.visualizar_dados(aba_nome="Visão Geral e Transações")
        if df.empty:
            return "Não há dados na planilha para analisar tendências."

        df["Data"] = pd.to_datetime(df["Data"])
        df["AnoMes"] = df["Data"].dt.to_period("M")

        df_despesas = df[df["Tipo (Receita/Despesa)"] == "Despesa"]

        if categoria:
            df_filtrado = df_despesas[
                df_despesas["Categoria"].astype(str).str.lower() == categoria.lower()
            ]
            if df_filtrado.empty:
                return f"Nenhuma despesa encontrada para a categoria '{categoria}'."
            tendencia = df_filtrado.groupby("AnoMes")["Valor"].sum().sort_index()
            return f"Tendência de gastos para a categoria '{categoria}':\n{tendencia.to_markdown()}"
        else:
            tendencia = df_despesas.groupby("AnoMes")["Valor"].sum().sort_index()
            return f"Tendência total de despesas por mês:\n{tendencia.to_markdown()}"
