from finance.domain.services.transaction_service import TransactionDomainService


class GetExpensesByCategoryUseCase:
    """
    Caso de Uso: Recuperar gastos agrupados por categoria.
    """

    def __init__(self, transaction_service: TransactionDomainService):
        self._service = transaction_service

    def execute(self, top_n: int = 5) -> dict[str, float]:
        return self._service.get_expenses_by_category(top_n=top_n)
