from datetime import datetime

from pydantic import BaseModel, Field


class Insight(BaseModel):
    """
    Entidade de Domínio representando um Insight da IA.
    """

    id: int | None = None
    date: datetime = Field(default_factory=datetime.now)
    type: str = Field(..., description="Tipo de Insight (Economia, Alerta, etc)")
    title: str = Field(..., description="Título Curto")
    details: str = Field(..., description="Conteúdo da Recomendação")
    status: str = Field("Novo", description="Novo, Lido, ou Concluído")

    def mark_as_read(self):
        """Marca o insight como lido."""
        if self.status == "Novo":
            self.status = "Lido"
