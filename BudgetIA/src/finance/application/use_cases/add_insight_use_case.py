from finance.domain.models.insight import Insight
from finance.domain.repositories.insight_repository import IInsightRepository


class AddInsightUseCase:
    """
    Caso de Uso: Adicionar um novo Insight da IA.
    """

    def __init__(self, repository: IInsightRepository):
        self._repository = repository

    def execute(self, insight: Insight) -> Insight:
        return self._repository.save(insight)
