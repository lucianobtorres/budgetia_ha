from typing import Any

from pydantic import BaseModel, Field

from core.base_tool import BaseTool
from core.logger import get_logger
from finance.domain.repositories.transaction_repository import ITransactionRepository

logger = get_logger("Tool_UpdTrans")
from collections.abc import Callable  # noqa: E402


class UpdateTransactionSchema(BaseModel):
    transaction_id: int = Field(
        ..., description="ID numérico da transação a ser atualizada."
    )
    data: str | None = Field(None, description="Nova data no formato YYYY-MM-DD.")
    tipo: str | None = Field(None, description="Novo tipo: 'Receita' ou 'Despesa'.")
    categoria: str | None = Field(
        None, description="Nova categoria (ex: Alimentação, Transporte)."
    )
    descricao: str | None = Field(None, description="Nova descrição da transação.")
    valor: float | None = Field(None, description="Novo valor numérico.")
    status: str | None = Field(
        None, description="Novo status (ex: Concluído, Pendente)."
    )


class UpdateTransactionTool(BaseTool):
    name = "update_transaction"
    description = "Atualiza/Edita campos de uma transação EXISTENTE. Use para corrigir erros ou alterar valores. NÃO use para novas transações."
    args_schema: type[BaseModel] = UpdateTransactionSchema

    # --- Injeção de Dependências ---
    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        save_func: Callable[[], None],
        recalculate_budgets_func: Callable[[], Any],
    ):
        self.transaction_repo = transaction_repo
        self.save = save_func
        self.recalculate_budgets = recalculate_budgets_func

    def run(self, transaction_id: int, **kwargs) -> str:
        logger.info(f"Ferramenta '{self.name}' chamada para ID={transaction_id}")
        try:
            # Filtra argumentos nulos
            dados_atualizados = {k: v for k, v in kwargs.items() if v is not None}

            if not dados_atualizados:
                return "Nenhuma alteração foi fornecida. Informe pelo menos um campo para atualizar."

            success = self.transaction_repo.update_transaction(
                transaction_id, dados_atualizados
            )

            if success:
                self.save()  # Persiste mudança
                self.recalculate_budgets()  # Atualiza orçamentos (gastos podem ter mudado)
                return f"Transação {transaction_id} atualizada com sucesso. Novos dados: {dados_atualizados}"

            return f"Transação {transaction_id} não encontrada para atualização."

        except Exception as e:
            return f"Erro ao atualizar transação: {str(e)}"
