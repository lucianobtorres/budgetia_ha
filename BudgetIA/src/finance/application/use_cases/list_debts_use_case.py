from finance.domain.models.debt import Debt
from finance.domain.repositories.debt_repository import IDebtRepository


class ListDebtsUseCase:
    """
    Caso de Uso para listar todas as dívidas do sistema.
    """

    def __init__(self, repository: IDebtRepository):
        self._repository = repository

    def execute(self) -> list[Debt]:
        return self._repository.list_all()
