from pydantic import BaseModel, Field


class Budget(BaseModel):
    """
    Entidade de Domínio representando um Orçamento por Categoria.
    Contém a lógica de saúde financeira do orçamento.
    """

    id: int | None = Field(None, description="Identificador único")
    categoria: str = Field(..., description="Categoria associada")
    limite: float = Field(..., description="Valor limite estabelecido")
    gasto_atual: float = Field(0.0, description="Valor já gasto no período")
    periodo: str = Field("Mensal", description="Frequência do orçamento")
    observacoes: str | None = Field(None, description="Notas adicionais")

    @property
    def percentual_gasto(self) -> float:
        """Calcula a porcentagem gasta em relação ao limite."""
        if self.limite <= 0:
            return 100.0 if self.gasto_atual > 0 else 0.0
        return round((self.gasto_atual / self.limite) * 100, 2)

    @property
    def status(self) -> str:
        """Determina o status de saúde do orçamento dinamicamente."""
        perc = self.percentual_gasto
        if perc > 100:
            return "Excedido"
        if perc > 80:
            return "Atenção"
        return "OK"

    @property
    def is_over_limit(self) -> bool:
        """Helper para verificar se o limite foi ultrapassado."""
        return self.gasto_atual > self.limite
