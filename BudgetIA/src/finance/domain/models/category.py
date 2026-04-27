from pydantic import BaseModel, Field, field_validator


class Category(BaseModel):
    """
    Entidade de Domínio representando uma Categoria de Transação.
    """

    name: str = Field(..., description="Nome da categoria")
    type: str = Field("Despesa", description="Tipo (Receita ou Despesa)")
    icon: str | None = Field(None, description="Emoji ou link do ícone")
    tags: str | None = Field(None, description="Tags separadas por vírgula")

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Remove espaços em branco extras."""
        if not v or not v.strip():
            raise ValueError("O nome da categoria não pode ser vazio.")
        return v.strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Valida se o tipo é permitido."""
        valid_types = ["Receita", "Despesa"]
        if v not in valid_types:
            raise ValueError(f"Tipo de categoria inválido: {v}. Deve ser {valid_types}")
        return v

    def __eq__(self, other) -> bool:
        """Comparação case-insensitive baseada no nome."""
        if not isinstance(other, Category):
            return False
        return self.name.lower() == other.name.lower()

    def __hash__(self) -> int:
        return hash(self.name.lower())
