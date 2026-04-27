from finance.domain.repositories.debt_repository import IDebtRepository


class DeleteDebtUseCase:
    """
    Caso de Uso para remover uma dívida do sistema.
    """

    def __init__(self, repository: IDebtRepository):
        self._repository = repository

    def execute(self, debt_id: int) -> bool:
        return self._repository.delete(debt_id)
