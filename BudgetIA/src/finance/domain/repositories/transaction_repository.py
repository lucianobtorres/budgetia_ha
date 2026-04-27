from abc import ABC, abstractmethod

from ..models.transaction import Transaction


class ITransactionRepository(ABC):
    """
    Interface (Contrato) para o repositório de Transações.
    Define como o domínio interage com a persistência de transações.
    """

    @abstractmethod
    def save(self, transaction: Transaction) -> Transaction:
        """Salva ou atualiza uma transação."""
        pass

    @abstractmethod
    def save_batch(self, transactions: list[Transaction]) -> int:
        """Salva múltiplas transações em lote."""
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Busca uma transação pelo ID."""
        pass

    @abstractmethod
    def delete(self, transaction_id: int) -> bool:
        """Remove uma transação pelo ID."""
        pass

    @abstractmethod
    def list_all(
        self, month: int | None = None, year: int | None = None
    ) -> list[Transaction]:
        """Lista transações, opcionalmente filtradas por mês/ano."""
        pass
