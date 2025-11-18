# Em: tests/services/test_debt_service.py

import pytest

from finance.services.debt_service import DebtService


@pytest.fixture
def debt_service() -> DebtService:
    """Retorna uma instância limpa do DebtService para cada teste."""
    return DebtService()


def test_calcular_saldo_devedor_atual_com_juros(
    debt_service: DebtService,
) -> None:
    """
    Testa o cálculo do Valor Presente (saldo devedor) com juros.
    """
    # ARRANGE
    taxa_juros = 1.0  # 1%
    parcelas_restantes = 12
    valor_parcela = 1000.0
    saldo_esperado = 11255.08  # Resultado de npf.pv(0.01, 12, -1000)

    # ACT
    saldo_calculado = debt_service.calcular_saldo_devedor_atual(
        valor_parcela=valor_parcela,
        taxa_juros_mensal=taxa_juros,
        parcelas_totais=24,
        parcelas_pagas=12,  # (24 - 12 = 12 restantes)
    )

    # ASSERT
    assert saldo_calculado == pytest.approx(saldo_esperado, abs=0.01)


def test_calcular_saldo_devedor_atual_sem_juros(
    debt_service: DebtService,
) -> None:
    """
    Testa o cálculo simples de multiplicação quando não há juros.
    """
    # ARRANGE
    taxa_juros = 0.0
    parcelas_restantes = 10
    valor_parcela = 150.0
    saldo_esperado = 1500.0  # (150 * 10)

    # ACT
    saldo_calculado = debt_service.calcular_saldo_devedor_atual(
        valor_parcela=valor_parcela,
        taxa_juros_mensal=taxa_juros,
        parcelas_totais=10,
        parcelas_pagas=0,
    )

    # ASSERT
    assert saldo_calculado == pytest.approx(saldo_esperado)


def test_calcular_saldo_devedor_quitado(debt_service: DebtService) -> None:
    """
    Testa se o saldo é zero quando não há parcelas restantes.
    """
    # ARRANGE
    taxa_juros = 1.0
    valor_parcela = 1000.0

    # ACT
    saldo_calculado = debt_service.calcular_saldo_devedor_atual(
        valor_parcela=valor_parcela,
        taxa_juros_mensal=taxa_juros,
        parcelas_totais=24,
        parcelas_pagas=24,  # Quitada!
    )

    # ASSERT
    assert saldo_calculado == 0.0
