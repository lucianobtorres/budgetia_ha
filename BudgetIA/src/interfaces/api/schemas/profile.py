from typing import Any

from pydantic import BaseModel, Field


class ProfileItemSchema(BaseModel):
    """Representa um item individual do perfil (campo/valor)."""

    campo: str = Field(..., alias="Campo")
    valor: Any = Field(..., alias="Valor")

    class Config:
        populate_by_name = True
