from pydantic import BaseModel
from tabulate import tabulate

import config
from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import VisualizarDadosPlanilhaInput


class VisualizarDadosPlanilhaTool(BaseTool):  # type: ignore[misc]
    name: str = "visualizar_dados_planilha"
    description: str = (
        "Retorna todos os dados atuais da Planilha Mestra em formato de texto para análise. "
        "Use esta ferramenta sempre que precisar de uma visão geral dos dados financeiros do usuário, "
        "transações, saldo, ou qualquer extrato da planilha."
    )
    args_schema: type[BaseModel] = VisualizarDadosPlanilhaInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self, aba_nome: str | None = None) -> str:
        if not self.planilha_manager:
            return "Erro: PlanilhaManager não inicializado."

        # Se a IA não especificar uma aba, mostramos a principal por padrão.
        if aba_nome is None:
            aba_nome = config.NomesAbas.TRANSACOES

        print(f"LOG: Ferramenta '{self.name}' foi chamada.")

        try:
            df = self.planilha_manager.visualizar_dados(aba_nome)
            if df.empty:
                return f"A aba '{aba_nome}' está vazia."

            # Converte o DataFrame para uma tabela bonita em formato Markdown
            return str(tabulate(df, headers="keys", tablefmt="pipe"))

        except Exception as e:
            return f"Ocorreu um erro ao visualizar os dados: {e}"
