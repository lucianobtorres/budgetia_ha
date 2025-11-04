from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import CalcularDespesasPorCategoriaInput


class CalcularDespesasPorCategoriaTool(BaseTool):  # type: ignore[misc]
    name: str = "calcular_despesas_por_categoria"
    description: str = (
        "Calcula e retorna as despesas totais agrupadas por categoria. "
        "Use esta ferramenta quando o usuário perguntar 'Onde eu gasto mais?', "
        "'Minhas despesas por tipo', 'Distribuição dos gastos'."
    )
    args_schema: type[BaseModel] = CalcularDespesasPorCategoriaInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self) -> str:
        print(f"LOG: Ferramenta '{self.name}' foi chamada.")
        df = self.planilha_manager.visualizar_dados(aba_nome="Visão Geral e Transações")
        if df.empty:
            return "Não há dados na planilha para calcular despesas por categoria."

        despesas_df = df[df["Tipo (Receita/Despesa)"] == "Despesa"]
        if despesas_df.empty:
            return "Não há despesas registradas na planilha."

        despesas_por_cat = (
            despesas_df.groupby("Categoria")["Valor"].sum().sort_values(ascending=False)
        )

        if despesas_por_cat.empty:
            return "Nenhuma despesa encontrada para categorização."

        return f"Despesas por Categoria:\n{despesas_por_cat.to_markdown()}"
