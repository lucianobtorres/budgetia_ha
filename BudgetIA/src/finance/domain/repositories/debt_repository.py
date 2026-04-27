from abc import ABC, abstractmethod

from ..models.debt import Debt


class IDebtRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Debt]:
        pass

    @abstractmethod
    def get_by_id(self, debt_id: int) -> Debt | None:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Debt | None:
        pass

    @abstractmethod
    def save(self, debt: Debt) -> Debt:
        pass

    @abstractmethod
    def delete(self, debt_id: int) -> bool:
        pass
