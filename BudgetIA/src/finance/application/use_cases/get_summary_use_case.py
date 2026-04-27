from finance.domain.services.transaction_service import TransactionDomainService


class GetSummaryUseCase:
    """
    Caso de Uso: Recuperar o resumo financeiro (Saldo, Receitas, Despesas).
    """

    def __init__(self, transaction_service: TransactionDomainService):
        self._service = transaction_service

    def execute(
        self, month: int | None = None, year: int | None = None
    ) -> dict[str, float]:
        return self._service.get_summary(month=month, year=year)
