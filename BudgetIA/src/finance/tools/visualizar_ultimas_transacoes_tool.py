# src/finance/tools/visualizar_ultimas_transacoes_tool.py


import pandas as pd
from pydantic import BaseModel, Field
from tabulate import tabulate

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager


class VisualizarUltimasTransacoesInput(BaseModel):
    n: int = Field(
        default=5, description="O número de últimas transações a serem visualizadas."
    )
    tipo: str | None = Field(
        default=None,
        description="Filtro opcional pelo tipo de transação: 'Receita' ou 'Despesa'.",
    )


class VisualizarUltimasTransacoesTool(BaseTool):
    name: str = "visualizar_ultimas_transacoes"
    description: str = (
        "Visualiza as 'n' últimas transações registradas, ordenadas por data. Pode ser filtrado por tipo ('Receita' ou 'Despesa')."
    )
    args_schema = VisualizarUltimasTransacoesInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self, n: int = 5, tipo: str | None = None) -> str:
        if not self.planilha_manager:
            return "Erro: PlanilhaManager não foi inicializado."

        try:
            df = self.planilha_manager.visualizar_dados(
                "Visão Geral e Transações"
            ).copy()
            if df.empty:
                return "Não há transações registradas na planilha."

            # Garante que a coluna de data seja do tipo datetime para ordenação correta
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

            # Filtra por tipo, se fornecido
            if tipo:
                df_filtrado = df[
                    df["Tipo (Receita/Despesa)"].str.lower() == tipo.lower()
                ]
            else:
                df_filtrado = df

            if df_filtrado.empty:
                return f"Não foram encontradas transações do tipo '{tipo}'."

            # Ordena por data (da mais recente para a mais antiga) e pega as 'n' últimas
            ultimas_transacoes = df_filtrado.sort_values(
                by="Data", ascending=False
            ).head(n)

            if ultimas_transacoes.empty:
                return "Não há transações para mostrar com os filtros aplicados."

            # Formata a saída como uma tabela de texto (Markdown)
            headers = ["Data", "Categoria", "Descricao", "Valor"]
            tabela = tabulate(
                ultimas_transacoes[headers],
                headers="keys",
                tablefmt="pipe",
                showindex=False,
            )

            return f"Suas {len(ultimas_transacoes)} últimas transações:\n{tabela}"
        except Exception as e:
            return f"Ocorreu um erro ao visualizar as últimas transações: {e}"
