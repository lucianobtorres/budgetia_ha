# src/finance/tools/define_budget_tool.py
from collections.abc import Callable  # Importar Callable

from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.schemas import DefinirOrcamentoInput

from core.logger import get_logger

logger = get_logger("Tool_DefineBudget")


class DefineBudgetTool(BaseTool):  # type: ignore[misc]
    name: str = "definir_orcamento"
    description: str = (
        "Define ou atualiza um orçamento para uma categoria específica na aba 'Meus Orçamentos'. "
        "Ex: 'Quero orçar R$500 para alimentação por mês'."
    )
    args_schema: type[BaseModel] = DefinirOrcamentoInput

    # --- DIP: Depende de Callables ---
    def __init__(
        self,
        add_budget_func: Callable[..., str],
        save_func: Callable[[], None],
    ) -> None:
        self.adicionar_ou_atualizar_orcamento = add_budget_func
        self.save = save_func

    # --- FIM DA MUDANÇA ---

    def run(
        self,
        categoria: str,
        valor_limite: float,
        periodo: str = "Mensal",
        observacoes: str = "",
    ) -> str:
        logger.info(
            f"Ferramenta '{self.name}' chamada para Categoria={categoria}, Limite={valor_limite}, Período={periodo}."
        )

        try:
            # --- DIP: Chama as funções injetadas ---
            mensagem = self.adicionar_ou_atualizar_orcamento(
                categoria=categoria,
                valor_limite=valor_limite,
                periodo=periodo,
                observacoes=observacoes,
            )
            self.save()  # Salva o orçamento
            return str(mensagem)
        except Exception as e:
            return f"Erro ao definir orçamento: {e}"
