from datetime import datetime

from pydantic import BaseModel, Field


class Debt(BaseModel):
    """
    Entidade de Domínio representando uma Dívida.
    """

    id: int | None = None
    nome: str = Field(..., description="Nome da Dívida")
    valor_original: float = Field(..., description="Valor Original")
    taxa_juros_mensal: float = Field(..., description="Taxa de Juros Mensal (%)")
    parcelas_totais: int = Field(..., description="Total de Parcelas")
    parcelas_pagas: int = Field(0, description="Parcelas Pagas")
    valor_parcela: float = Field(..., description="Valor da Parcela")
    saldo_devedor_atual: float = Field(0.0, description="Saldo Devedor Atual")
    data_proximo_pgto: datetime | None = None
    data_inicio: datetime | None = None
    observacoes: str = ""

    def calculate_current_balance(self) -> float:
        """
        Calcula o saldo devedor atual (Valor Presente) usando juros compostos.
        """
        remaining = self.parcelas_totais - self.parcelas_pagas
        if remaining <= 0:
            return 0.0

        if self.taxa_juros_mensal <= 0:
            return float(remaining * self.valor_parcela)

        try:
            import numpy_financial as npf

            rate = self.taxa_juros_mensal / 100.0
            pv = npf.pv(rate=rate, nper=remaining, pmt=-self.valor_parcela, when="end")
            return float(pv)
        except ImportError:
            # Fallback se numpy_financial não estiver disponível
            return float(remaining * self.valor_parcela)
        except Exception:
            return float(remaining * self.valor_parcela)

    def mark_installment_paid(self):
        """Registra o pagamento de uma parcela."""
        if self.parcelas_pagas < self.parcelas_totais:
            self.parcelas_pagas += 1
            self.saldo_devedor_atual = self.calculate_current_balance()
