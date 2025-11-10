# src/finance/tools/calculate_expenses_by_category_tool.py
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel

from config import ColunasTransacoes, ValoresTipo
from core.base_tool import BaseTool
from finance.schemas import CalcularDespesasPorCategoriaInput


class CalcularDespesasPorCategoriaTool(BaseTool):  # type: ignore[misc]
    name: str = "calcular_despesas_por_categoria"
    description: str = (
        "Calcula e retorna as despesas totais agrupadas por categoria. "
        "Use esta ferramenta quando o usuário perguntar 'Onde eu gasto mais?', "
        "'Minhas despesas por tipo', 'Distribuição dos gastos'."
    )
    args_schema: type[BaseModel] = CalcularDespesasPorCategoriaInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self) -> str:
        print(f"LOG: Ferramenta '{self.name}' foi chamada.")

        # --- DIP: Chama a função injetada ---
        df = self.visualizar_dados(aba_nome="Visão Geral e Transações")
        if df.empty:
            return "Não há dados na planilha para calcular despesas por categoria."

        despesas_df = df[df[ColunasTransacoes.TIPO] == ValoresTipo.DESPESA]
        if despesas_df.empty:
            return "Não há despesas registradas na planilha."

        despesas_por_cat = (
            despesas_df.groupby(ColunasTransacoes.CATEGORIA)[ColunasTransacoes.VALOR]
            .sum()
            .sort_values(ascending=False)
        )

        if despesas_por_cat.empty:
            return "Nenhuma despesa encontrada para categorização."

        return f"Despesas por Categoria:\n{despesas_por_cat.to_markdown()}"
