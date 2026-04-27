from finance.domain.repositories.budget_repository import IBudgetRepository
from finance.domain.services.budget_service import BudgetDomainService


class DeleteBudgetUseCase:
    def __init__(
        self, repository: IBudgetRepository, budget_service: BudgetDomainService
    ):
        self._repository = repository
        self._budget_service = budget_service

    def execute(self, budget_id: int) -> bool:
        success = self._repository.delete(budget_id)
        if success:
            # Recalcula para garantir que os gastos estejam atualizados se um orçamento sumiu?
            # Na verdade deletar um orçamento não muda as transações, mas o "status" dos outros não muda.
            # Mas vamos manter o padrão de recálculo se necessário.
            self._budget_service.recalculate_budgets()
        return success
