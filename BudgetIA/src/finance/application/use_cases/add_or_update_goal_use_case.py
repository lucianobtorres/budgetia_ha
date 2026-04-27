from finance.domain.models.goal import Goal
from finance.domain.repositories.goal_repository import IGoalRepository


class AddOrUpdateGoalUseCase:
    """
    Caso de Uso: Adicionar ou Atualizar uma Meta Financeira.
    Contém a lógica de orquestração para persistência de metas.
    """

    def __init__(self, repository: IGoalRepository):
        self._repository = repository

    def execute(self, goal: Goal) -> Goal:
        # Lógica adicional poderia ser adicionada aqui no futuro
        # (ex: validar se o valor alvo é coerente com a renda do perfil)
        return self._repository.save(goal)
