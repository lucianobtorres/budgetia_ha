from abc import ABC, abstractmethod

from ..models.budget import Budget


class IBudgetRepository(ABC):
    """
    Interface (Contrato) para o repositório de Orçamentos.
    """

    @abstractmethod
    def save(self, budget: Budget) -> Budget:
        """Salva ou atualiza um orçamento."""
        pass

    @abstractmethod
    def get_by_id(self, budget_id: int) -> Budget | None:
        """Busca um orçamento pelo ID."""
        pass

    @abstractmethod
    def get_by_category(self, category: str) -> Budget | None:
        """Busca um orçamento pela categoria (chave de negócio)."""
        pass

    @abstractmethod
    def list_all(self) -> list[Budget]:
        """Lista todos os orçamentos."""
        pass

    @abstractmethod
    def delete(self, budget_id: int) -> bool:
        """Remove um orçamento."""
        pass
