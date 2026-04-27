from datetime import date

from pydantic import BaseModel


class GoalBase(BaseModel):
    nome: str
    valor_alvo: float
    valor_atual: float = 0.0
    data_alvo: date | None = None
    status: str = "Em Andamento"
    observacoes: str | None = ""


class GoalCreate(GoalBase):
    pass


class GoalSchema(GoalBase):
    id: int
    percentual_progresso: float

    class Config:
        from_attributes = True
