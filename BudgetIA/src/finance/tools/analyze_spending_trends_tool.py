# src/finance/tools/analyze_spending_trends_tool.py
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.schemas import AnalisarTendenciasGastosInput


class AnalisarTendenciasGastosTool(BaseTool):  # type: ignore[misc]
    name: str = "analisar_tendencias_gastos"
    description: str = (
        "Analisa e retorna as tendências de gastos ao longo do tempo, opcionalmente por categoria. "
        "Útil para identificar se os gastos estão aumentando ou diminuindo."
    )
    args_schema: type[BaseModel] = AnalisarTendenciasGastosInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self, categoria: str | None = None) -> str:
        print(f"LOG: Ferramenta '{self.name}' chamada para Categoria={categoria}.")

        # --- DIP: Chama a função injetada ---
        df = self.visualizar_dados(aba_nome="Visão Geral e Transações")
        if df.empty:
            return "Não há dados na planilha para analisar tendências."

        try:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
            df.dropna(subset=["Data"], inplace=True)  # Remove linhas sem data válida
            df["AnoMes"] = df["Data"].dt.to_period("M")
        except Exception as e:
            return f"Erro ao processar datas da planilha: {e}"

        df_despesas = df[df["Tipo (Receita/Despesa)"] == "Despesa"]
        if df_despesas.empty:
            return "Não há despesas registradas para analisar."

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
            if tendencia.empty:
                return "Não há dados de despesa suficientes para calcular a tendência."
            return f"Tendência total de despesas por mês:\n{tendencia.to_markdown()}"
