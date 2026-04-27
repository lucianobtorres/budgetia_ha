from datetime import date

from pydantic import BaseModel, Field, field_validator


class Transaction(BaseModel):
    """
    Entidade de Domínio representando uma Transação Financeira.
    Contém regras de negócio e validações intrínsecas.
    """

    id: int | None = Field(None, description="Identificador único da transação")
    data: date = Field(..., description="Data da ocorrência")
    tipo: str = Field(..., description="Tipo: Receita ou Despesa")
    categoria: str = Field(..., description="Categoria da transação")
    descricao: str = Field(..., description="Descrição resumida")
    valor: float = Field(..., description="Valor monetário positivo")
    status: str = Field("Concluído", description="Status da transação")
    id_externo: str | None = Field(
        None, description="ID de referência externa (opcional)"
    )

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Valor deve ser positivo")
        return v

    @field_validator("descricao", mode="before")
    @classmethod
    def normalizar_descricao(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @property
    def eh_despesa(self) -> bool:
        """Helper para verificar se é uma despesa."""
        return self.tipo.lower() == "despesa"

    def eh_assinatura(self, palavras_chave: list[str]) -> bool:
        """
        Lógica de domínio: Verifica se esta transação se comporta como uma assinatura
        baseado em uma lista de palavras-chave fornecida.
        """
        if not self.eh_despesa:
            return False

        desc_lower = self.descricao.lower()
        return any(kw.lower() in desc_lower for kw in palavras_chave)
