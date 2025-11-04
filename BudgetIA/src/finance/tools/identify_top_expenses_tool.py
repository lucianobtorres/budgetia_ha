from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import IdentificarMaioresGastosInput


class IdentificarMaioresGastosTool(BaseTool):  # type: ignore[misc]
    name: str = "identificar_maiores_gastos"
    description: str = (
        "Identifica e retorna as N maiores despesas individuais na planilha, útil para encontrar gastos significativos. "
        "Use esta ferramenta quando o usuário perguntar 'Quais foram meus maiores gastos?', 'Me mostre os gastos mais altos'."
    )
    args_schema: type[BaseModel] = IdentificarMaioresGastosInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self, top_n: int = 3) -> str:
        print(f"LOG: Ferramenta '{self.name}' foi chamada com top_n={top_n}.")
        df = self.planilha_manager.visualizar_dados(aba_nome="Visão Geral e Transações")
        if df.empty:
            return "Não há dados na planilha para identificar os maiores gastos."

        despesas_df = df[df["Tipo (Receita/Despesa)"] == "Despesa"]
        if despesas_df.empty:
            return "Não há despesas registradas na planilha."

        maiores_gastos = despesas_df.nlargest(top_n, "Valor")

        if maiores_gastos.empty:
            return "Nenhum gasto significativo encontrado."

        # Seleciona colunas relevantes para o LLM
        maiores_gastos_selecionados = maiores_gastos[
            ["Data", "Categoria", "Descricao", "Valor"]
        ]

        return f"Seus {top_n} maiores gastos individuais:\n{maiores_gastos_selecionados.to_markdown(index=False)}"
