from typing import Any

from pydantic import BaseModel


class ToolInfoSchema(BaseModel):
    """Informações sobre uma ferramenta da IA."""

    name: str
    description: str
    label: str | None = None
    is_essential: bool


class ObserverInfoSchema(BaseModel):
    """Informações sobre um observador proativo (regra)."""

    id: str
    name: str
    description: str
    is_active: bool
    config: dict[str, Any] = {}


class SubscriptionKeywordsUpdate(BaseModel):
    """Payload para atualizar palavras-chave de assinatura."""

    keywords: list[str]
