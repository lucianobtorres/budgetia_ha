from finance.domain.models.transaction import Transaction
from finance.domain.repositories.transaction_repository import ITransactionRepository
from finance.domain.services.budget_service import BudgetDomainService


class UpdateTransactionUseCase:
    """
    Caso de Uso: Atualizar uma transação existente.
    """

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        budget_service: BudgetDomainService,
    ):
        self._transaction_repo = transaction_repo
        self._budget_service = budget_service

    def execute(self, transaction: Transaction) -> Transaction | None:
        # 1. Busca a original para saber se mudou o mês/ano (precisa recalcular ambos se mudou)
        original = self._transaction_repo.get_by_id(transaction.id)  # type: ignore
        if not original:
            return None

        # 2. Salva a nova versão
        updated = self._transaction_repo.save(transaction)

        # 3. Recalcula o mês atual
        self._budget_service.recalculate_budgets(updated.data.month, updated.data.year)

        # 4. Se o mês/ano mudou, recalcula o original também
        if (
            original.data.month != updated.data.month
            or original.data.year != updated.data.year
        ):
            self._budget_service.recalculate_budgets(
                original.data.month, original.data.year
            )

        return updated
