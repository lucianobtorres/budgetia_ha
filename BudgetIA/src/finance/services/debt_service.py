# Em: src/finance/services/debt_service.py

import numpy_financial as npf
from core.logger import get_logger

logger = get_logger("DebtService")


class DebtService:
    """
    Classe especialista em realizar cálculos puros de Dívidas.
    Não possui estado.
    """

    def calcular_saldo_devedor_atual(
        self,
        valor_parcela: float,
        taxa_juros_mensal: float,
        parcelas_totais: int,
        parcelas_pagas: int,
    ) -> float:
        """
        Calcula o Saldo Devedor Atual (PV) de um financiamento.
        (Este é o método movido do FinancialCalculator)
        """
        if taxa_juros_mensal <= 0:
            return float(valor_parcela * (parcelas_totais - parcelas_pagas))

        taxa_decimal = taxa_juros_mensal / 100.0
        parcelas_restantes = parcelas_totais - parcelas_pagas

        if parcelas_restantes <= 0:
            return 0.0

        try:
            saldo_devedor = npf.pv(
                rate=taxa_decimal,
                nper=parcelas_restantes,
                pmt=-valor_parcela,
                when="end",
            )
            return float(saldo_devedor)
        except Exception as e:
            # Fallback em caso de erro no cálculo (ex: npf não disponível)
            logger.error(f"Erro ao calcular PV: {e}")
            return float(valor_parcela * parcelas_restantes)
