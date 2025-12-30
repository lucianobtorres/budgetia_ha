# src/finance/tools/view_debts_tool.py
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel

from config import NomesAbas
from core.base_tool import BaseTool
from finance.schemas import VisualizarDividasInput

from core.logger import get_logger

logger = get_logger("Tool_ViewDebts")


class VisualizarDividasTool(BaseTool):  # type: ignore[misc]
    name: str = "visualizar_dividas"
    description: str = (
        "Retorna todos os dados atuais da aba 'Minhas Dívidas' em formato de texto para análise. "
        "Use para 'Quais são minhas dívidas?', 'Qual o saldo das minhas dívidas?'."
    )
    args_schema: type[BaseModel] = VisualizarDividasInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self) -> str:
        logger.info(f"Ferramenta '{self.name}' foi chamada.")

        # --- DIP: Chama a função injetada ---
        df = self.visualizar_dados(aba_nome=NomesAbas.DIVIDAS)
        if df.empty:
            return "A aba de dívidas está vazia. Nenhuma dívida encontrada."

        # Formata para o LLM
        return f"Minhas Dívidas:\n{df.to_markdown(index=False)}"
