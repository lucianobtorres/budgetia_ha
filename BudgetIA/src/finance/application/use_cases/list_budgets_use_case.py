from finance.domain.models.budget import Budget
from finance.domain.repositories.budget_repository import IBudgetRepository


class ListBudgetsUseCase:
    """
    Caso de Uso para listar todos os orçamentos do sistema.
    """

    def __init__(self, repository: IBudgetRepository):
        self._repository = repository

    def execute(self) -> list[Budget]:
        return self._repository.list_all()
