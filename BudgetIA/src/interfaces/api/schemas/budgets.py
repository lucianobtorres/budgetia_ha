from pydantic import BaseModel, Field


class BudgetSchema(BaseModel):
    """Esquema para um orçamento financeiro."""

    id: int | None = Field(None, alias="ID Orcamento")
    categoria: str = Field(..., alias="Categoria")
    valor_limite: float = Field(..., alias="Valor Limite")
    valor_gasto_atual: float = Field(0.0, alias="Valor Gasto Atual")
    porcentagem_gasta: float = Field(0.0, alias="Porcentagem Gasta (%)")
    periodo: str = Field("Mensal", alias="Período Orçamento")
    status: str | None = Field("Ativo", alias="Status Orçamento")
    observacoes: str | None = Field("", alias="Observações")
    ultima_atualizacao: str | None = Field(None, alias="Última Atualização Orçamento")

    class Config:
        populate_by_name = True


class BudgetCreate(BaseModel):
    """Esquema para criação de um novo orçamento."""

    categoria: str
    valor_limite: float
    periodo: str = "Mensal"
    observacoes: str | None = ""


class BudgetUpdate(BudgetCreate):
    """Esquema para atualização de orçamento existente."""

    pass
