from typing import Any

from finance.domain.models.budget import Budget
from finance.domain.repositories.budget_repository import IBudgetRepository
from finance.domain.services.budget_service import BudgetDomainService


class UpdateBudgetUseCase:
    def __init__(
        self, repository: IBudgetRepository, budget_service: BudgetDomainService
    ):
        self._repository = repository
        self._budget_service = budget_service

    def execute(self, budget_id: int, data: dict[str, Any]) -> bool:
        existing = self._repository.get_by_id(budget_id)
        if not existing:
            return False

        updated_data = existing.model_dump()
        updated_data.update(data)

        updated_entity = Budget(**updated_data)
        self._repository.save(updated_entity)

        self._budget_service.recalculate_budgets()
        return True
