from abc import ABC, abstractmethod

from ..models.category import Category


class ICategoryRepository(ABC):
    """
    Interface (Contrato) para o repositório de Categorias.
    """

    @abstractmethod
    def list_all(self) -> list[Category]:
        """Retorna todas as categorias cadastradas."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Category | None:
        """Busca uma categoria pelo nome (case-insensitive)."""
        pass

    @abstractmethod
    def save(self, category: Category) -> Category:
        """Salva ou atualiza uma categoria."""
        pass

    @abstractmethod
    def delete(self, name: str) -> bool:
        """Remove uma categoria pelo nome."""
        pass
