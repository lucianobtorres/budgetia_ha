from finance.domain.repositories.goal_repository import IGoalRepository


class DeleteGoalUseCase:
    """
    Caso de Uso: Deletar uma Meta Financeira.
    """

    def __init__(self, repository: IGoalRepository):
        self._repository = repository

    def execute(self, goal_id: int) -> bool:
        return self._repository.delete(goal_id)
