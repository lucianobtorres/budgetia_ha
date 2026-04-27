from finance.domain.models.transaction import Transaction
from finance.domain.repositories.transaction_repository import ITransactionRepository
from finance.domain.services.budget_service import BudgetDomainService


class AddTransactionUseCase:
    """
    Caso de Uso: Adicionar uma nova transação.
    Orquestra a persistência e o recálculo dos orçamentos afetados.
    """

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        budget_service: BudgetDomainService,
    ):
        self._transaction_repo = transaction_repo
        self._budget_service = budget_service

    def execute(self, transaction: Transaction) -> Transaction:
        # 1. Salva a transação
        saved_transaction = self._transaction_repo.save(transaction)

        # 2. Recalcula orçamentos para o mês/ano da transação
        self._budget_service.recalculate_budgets(
            month=saved_transaction.data.month, year=saved_transaction.data.year
        )

        return saved_transaction
