from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import DefinirOrcamentoInput


class DefineBudgetTool(BaseTool):  # type: ignore[misc]
    name: str = "definir_orcamento"
    description: str = (
        "Define ou atualiza um orçamento para uma categoria específica na aba 'Meus Orçamentos'. "
        "Útil para o usuário estabelecer ou modificar limites de gastos. "
        "Ex: 'Quero orçar R$500 para alimentação por mês'."
    )
    args_schema: type[BaseModel] = DefinirOrcamentoInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(
        self,
        categoria: str,
        valor_limite: float,
        periodo: str = "Mensal",
        observacoes: str = "",
    ) -> str:
        if not self.planilha_manager:
            return "Erro..."
        print(
            f"LOG: Ferramenta '{self.name}' chamada para Categoria={categoria}, Limite={valor_limite}, Período={periodo}."
        )
        if not self.planilha_manager:
            return "Erro: PlanilhaManager não inicializado."

        try:
            mensagem = self.planilha_manager.adicionar_ou_atualizar_orcamento(
                categoria=categoria,
                valor_limite=valor_limite,
                periodo=periodo,
                observacoes=observacoes,
            )
            self.planilha_manager.save()
            return str(mensagem)
        except Exception as e:
            return f"Erro ao definir orçamento: {e}"
