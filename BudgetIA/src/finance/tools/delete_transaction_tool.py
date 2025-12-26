from typing import Type, Callable, Any
from pydantic import BaseModel, Field
from core.base_tool import BaseTool
from finance.repositories.transaction_repository import TransactionRepository

class DeleteTransactionSchema(BaseModel):
    transaction_id: int = Field(..., description="ID numérico da transação a ser excluída.")

class DeleteTransactionTool(BaseTool):
    name = "delete_transaction"
    description = "Exclui PERMANENTEMENTE uma transação da planilha financeira usando seu ID."
    args_schema: Type[BaseModel] = DeleteTransactionSchema

    # --- Injeção de Dependências ---
    def __init__(
        self, 
        transaction_repo: TransactionRepository,
        save_func: Callable[[], None],
        recalculate_budgets_func: Callable[[], Any]
    ):
        self.transaction_repo = transaction_repo
        self.save = save_func
        self.recalculate_budgets = recalculate_budgets_func

    def run(self, transaction_id: int) -> str:
        try:
            success = self.transaction_repo.delete_transaction(transaction_id)
            if success:
                self.save() # Salva no disco/nuvem
                self.recalculate_budgets() # Atualiza orçamentos (gastos podem ter diminuído)
                return f"Transação {transaction_id} excluída com sucesso."
                
            return f"Não foi possível encontrar uma transação com o ID {transaction_id}."
        except Exception as e:
            return f"Erro ao excluir transação: {str(e)}"
