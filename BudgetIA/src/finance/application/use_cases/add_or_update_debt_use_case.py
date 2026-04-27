from finance.domain.models.debt import Debt
from finance.domain.repositories.debt_repository import IDebtRepository


class AddOrUpdateDebtUseCase:
    """
    Caso de Uso: Adicionar ou Atualizar uma Dívida.
    """

    def __init__(self, repository: IDebtRepository):
        self._repository = repository

    def execute(self, debt: Debt) -> Debt:
        # 1. Busca existente se ID for nulo (pelo nome)
        if debt.id is None:
            existing = self._repository.get_by_name(debt.nome)
            if existing:
                debt.id = existing.id

        # 2. A própria entidade rica calcula o saldo
        debt.saldo_devedor_atual = debt.calculate_current_balance()

        # 3. Salva
        return self._repository.save(debt)
