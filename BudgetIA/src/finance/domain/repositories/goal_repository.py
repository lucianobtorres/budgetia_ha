from abc import ABC, abstractmethod

from ..models.goal import Goal


class IGoalRepository(ABC):
    """Interface abstrata para persistência de Metas Financeiras."""

    @abstractmethod
    def save(self, goal: Goal) -> Goal:
        """Salva ou atualiza uma meta."""
        pass

    @abstractmethod
    def get_by_id(self, goal_id: int) -> Goal | None:
        """Busca uma meta pelo ID."""
        pass

    @abstractmethod
    def list_all(self) -> list[Goal]:
        """Lista todas as metas cadastradas."""
        pass

    @abstractmethod
    def delete(self, goal_id: int) -> bool:
        """Remove uma meta pelo ID."""
        pass
