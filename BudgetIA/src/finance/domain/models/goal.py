from datetime import date

from pydantic import BaseModel, Field, computed_field


class Goal(BaseModel):
    """
    Entidade de Domínio que representa uma Meta Financeira.
    Ex: 'Comprar um Carro', 'Reserva de Emergência'.
    """

    id: int | None = None
    nome: str
    valor_alvo: float = Field(gt=0, description="Quanto o usuário quer atingir")
    valor_atual: float = Field(
        default=0.0, ge=0, description="Quanto o usuário já economizou"
    )
    data_alvo: date | None = None
    status: str = "Em Andamento"
    observacoes: str | None = ""

    @computed_field
    @property
    def percentual_progresso(self) -> float:
        """Calcula a porcentagem concluída da meta."""
        if self.valor_alvo <= 0:
            return 0.0
        progresso = (self.valor_atual / self.valor_alvo) * 100
        return round(min(progresso, 100.0), 2)

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Verifica se a meta foi atingida."""
        return self.valor_atual >= self.valor_alvo

    def update_progress(self, new_value: float):
        """Atualiza o valor atual e ajusta o status se necessário."""
        self.valor_atual = new_value
        if self.is_completed:
            self.status = "Concluída"
        elif self.status == "Concluída" and not self.is_completed:
            self.status = "Em Andamento"
