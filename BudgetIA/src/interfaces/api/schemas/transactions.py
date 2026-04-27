from pydantic import BaseModel, Field


class TransactionSchema(BaseModel):
    """Esquema base para uma transação financeira."""

    id: int | None = Field(None, alias="ID Transacao")
    data: str = Field(
        ..., alias="Data", description="Data no formato YYYY-MM-DD ou DD/MM/YYYY"
    )
    tipo: str = Field(..., alias="Tipo (Receita/Despesa)")
    categoria: str = Field(..., alias="Categoria")
    descricao: str = Field(..., alias="Descricao")
    valor: float = Field(..., alias="Valor")
    status: str = Field("Concluído", alias="Status")

    class Config:
        populate_by_name = True


class TransactionCreate(BaseModel):
    """Esquema para criação de nova transação."""

    data: str | None = None
    tipo: str
    categoria: str
    descricao: str
    valor: float
    status: str = "Concluído"
    parcelas: int = 1


class TransactionUpdate(TransactionCreate):
    """Esquema para atualização de transação existente."""

    pass
