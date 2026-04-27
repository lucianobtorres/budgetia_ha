from finance.domain.models.goal import Goal
from finance.domain.repositories.goal_repository import IGoalRepository


class ListGoalsUseCase:
    """
    Caso de Uso: Listar Metas Financeiras.
    """

    def __init__(self, repository: IGoalRepository):
        self._repository = repository

    def execute(self) -> list[Goal]:
        return self._repository.list_all()
