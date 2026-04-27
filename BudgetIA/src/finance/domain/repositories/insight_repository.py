from abc import ABC, abstractmethod

from ..models.insight import Insight


class IInsightRepository(ABC):
    @abstractmethod
    def list_all(self, status: str | None = None) -> list[Insight]:
        pass

    @abstractmethod
    def save(self, insight: Insight) -> Insight:
        pass

    @abstractmethod
    def update_status(self, insight_id: int, new_status: str) -> bool:
        pass

    @abstractmethod
    def delete_old_insights(self, days: int) -> int:
        pass
