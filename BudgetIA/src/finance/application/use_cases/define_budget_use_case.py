from finance.domain.models.budget import Budget
from finance.domain.repositories.budget_repository import IBudgetRepository
from finance.domain.services.budget_service import BudgetDomainService


class DefineBudgetUseCase:
    """
    Caso de Uso: Definir (criar ou atualizar) um orçamento.
    """

    def __init__(
        self, budget_repo: IBudgetRepository, budget_service: BudgetDomainService
    ):
        self._budget_repo = budget_repo
        self._budget_service = budget_service

    def execute(self, budget: Budget) -> Budget:
        # 1. Tenta encontrar existente para evitar duplicidade por categoria
        existing = self._budget_repo.get_by_category(budget.categoria)

        if existing:
            # Merge de dados para manter o ID
            existing.limite = budget.limite
            existing.periodo = budget.periodo
            existing.observacoes = budget.observacoes
            budget_to_save = existing
        else:
            budget_to_save = budget

        # 2. Salva
        saved = self._budget_repo.save(budget_to_save)

        # 3. Recalcula
        self._budget_service.recalculate_budgets()

        return saved
