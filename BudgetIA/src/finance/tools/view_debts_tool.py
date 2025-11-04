from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import VisualizarDividasInput


class VisualizarDividasTool(BaseTool):  # type: ignore[misc]
    name: str = "visualizar_dividas"
    description: str = (
        "Retorna todos os dados atuais da aba 'Minhas Dívidas' em formato de texto para análise. "
        "Use esta ferramenta para responder perguntas sobre as dívidas do usuário, "
        "como 'Quais são minhas dívidas?', 'Qual o saldo das minhas dívidas?'. "
        "Retorna uma string formatada dos dados da planilha ou uma mensagem de vazio."
    )
    args_schema: type[BaseModel] = VisualizarDividasInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self) -> str:
        print(f"LOG: Ferramenta '{self.name}' foi chamada.")
        df = self.planilha_manager.visualizar_dados(aba_nome="Minhas Dívidas")
        if df.empty:
            return "A aba de dívidas está vazia. Nenhuma dívida encontrada."

        # Formata para o LLM
        return f"Minhas Dívidas:\n{df.to_markdown(index=False)}"
