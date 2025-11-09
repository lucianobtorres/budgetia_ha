# src/finance/tools/view_data_tool.py
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel
from tabulate import tabulate

import config
from core.base_tool import BaseTool
from finance.schemas import VisualizarDadosPlanilhaInput


class VisualizarDadosPlanilhaTool(BaseTool):  # type: ignore[misc]
    name: str = "visualizar_dados_planilha"
    description: str = (
        "Retorna todos os dados de uma aba específica da Planilha Mestra em formato de texto. "
        "Use esta ferramenta sempre que precisar de uma visão geral dos dados, transações, etc."
    )
    args_schema: type[BaseModel] = VisualizarDadosPlanilhaInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self, aba_nome: str | None = None) -> str:
        if aba_nome is None:
            aba_nome = config.NomesAbas.TRANSACOES

        print(f"LOG: Ferramenta '{self.name}' foi chamada para a aba '{aba_nome}'.")

        try:
            # --- DIP: Chama a função injetada ---
            df = self.visualizar_dados(aba_nome=aba_nome)
            if df.empty:
                return f"A aba '{aba_nome}' está vazia."

            # Converte o DataFrame para uma tabela bonita em formato Markdown
            return str(tabulate(df, headers="keys", tablefmt="pipe", showindex=False))

        except Exception as e:
            return f"Ocorreu um erro ao visualizar os dados da aba '{aba_nome}': {e}"
