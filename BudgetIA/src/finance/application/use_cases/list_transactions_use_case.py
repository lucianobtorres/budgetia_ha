from finance.domain.models.transaction import Transaction
from finance.domain.repositories.transaction_repository import ITransactionRepository


class ListTransactionsUseCase:
    """
    Caso de Uso para listar transações com suporte a filtros e limites.
    """

    def __init__(self, repository: ITransactionRepository):
        self._repository = repository

    def execute(
        self, month: int | None = None, year: int | None = None, limit: int = 100
    ) -> list[Transaction]:
        # 1. Obtém do repositório (filtros de tempo já aplicados no repo se fornecidos)
        transactions = self._repository.list_all(month=month, year=year)

        # 2. Ordena por data (mais recente primeiro)
        transactions.sort(key=lambda x: x.data, reverse=True)

        # 3. Aplica limite se não for filtro de período específico (ou aplica sempre)
        if month is None or year is None:
            return transactions[:limit]

        # Se for período, retornamos tudo do período (limitado a um teto de segurança)
        return transactions[:1000]
