# src/core/base_tool.py
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseTool(ABC):
    """Classe base abstrata e simplificada para todas as ferramentas."""

    name: str
    description: str
    args_schema: type[BaseModel]

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        pass
