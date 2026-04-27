from finance.domain.repositories.transaction_repository import ITransactionRepository
from finance.domain.services.budget_service import BudgetDomainService


class DeleteTransactionUseCase:
    """
    Caso de Uso: Deletar uma transação.
    """

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        budget_service: BudgetDomainService,
    ):
        self._transaction_repo = transaction_repo
        self._budget_service = budget_service

    def execute(self, transaction_id: int) -> bool:
        # 1. Busca antes de deletar para saber qual mês/ano recalcular
        transaction = self._transaction_repo.get_by_id(transaction_id)
        if not transaction:
            return False

        # 2. Deleta
        success = self._transaction_repo.delete(transaction_id)

        # 3. Recalcula se teve sucesso
        if success:
            self._budget_service.recalculate_budgets(
                month=transaction.data.month, year=transaction.data.year
            )

        return success
