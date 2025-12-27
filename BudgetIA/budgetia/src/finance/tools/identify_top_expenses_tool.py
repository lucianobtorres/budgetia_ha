# src/finance/tools/identify_top_expenses_tool.py
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel

from config import ColunasTransacoes, NomesAbas, ValoresTipo
from core.base_tool import BaseTool
from finance.schemas import IdentificarMaioresGastosInput


class IdentificarMaioresGastosTool(BaseTool):  # type: ignore[misc]
    name: str = "identificar_maiores_gastos"
    description: str = (
        "Identifica e retorna as N maiores despesas individuais na planilha, útil para encontrar gastos significativos."
    )
    args_schema: type[BaseModel] = IdentificarMaioresGastosInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self, top_n: int = 3) -> str:
        print(f"LOG: Ferramenta '{self.name}' foi chamada com top_n={top_n}.")

        # --- DIP: Chama a função injetada ---
        df = self.visualizar_dados(sheet_name=NomesAbas.TRANSACOES)
        if df.empty:
            return "Não há dados na planilha para identificar os maiores gastos."

        despesas_df = df[df[ColunasTransacoes.TIPO] == ValoresTipo.DESPESA]
        if despesas_df.empty:
            return "Não há despesas registradas na planilha."

        try:
            # Garantir que 'Valor' é numérico para nlargest
            despesas_df[ColunasTransacoes.VALOR] = pd.to_numeric(
                despesas_df[ColunasTransacoes.VALOR], errors="coerce"
            )
            despesas_df.dropna(subset=[ColunasTransacoes.VALOR], inplace=True)

            maiores_gastos = despesas_df.nlargest(top_n, ColunasTransacoes.VALOR)
        except Exception as e:
            return f"Erro ao processar valores das despesas: {e}"

        if maiores_gastos.empty:
            return f"Nenhum gasto significativo encontrado (top_n={top_n})."

        colunas_relevantes = [
            ColunasTransacoes.DATA,
            ColunasTransacoes.CATEGORIA,
            ColunasTransacoes.DESCRICAO,
            ColunasTransacoes.VALOR,
        ]
        # Filtra colunas que realmente existem no DF
        colunas_para_mostrar = [
            col for col in colunas_relevantes if col in maiores_gastos.columns
        ]

        maiores_gastos_selecionados = maiores_gastos[colunas_para_mostrar]

        return f"Seus {top_n} maiores gastos individuais:\n{maiores_gastos_selecionados.to_markdown(index=False)}"
