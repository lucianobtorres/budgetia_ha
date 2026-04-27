from datetime import date

from pydantic import BaseModel


class DebtBase(BaseModel):
    nome: str
    valor_original: float
    taxa_juros_mensal: float
    parcelas_totais: int
    parcelas_pagas: int = 0
    valor_parcela: float
    data_proximo_pgto: date | None = None
    observacoes: str | None = ""


class DebtCreate(DebtBase):
    pass


class DebtSchema(DebtBase):
    id: int
    saldo_devedor_atual: float

    class Config:
        from_attributes = True
