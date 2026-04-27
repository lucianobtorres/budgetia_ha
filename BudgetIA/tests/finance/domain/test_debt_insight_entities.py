from finance.domain.models.debt import Debt
from finance.domain.models.insight import Insight


def test_debt_balance_calculation_simple():
    """Testa cálculo de saldo sem juros."""
    debt = Debt(
        nome="Empréstimo Amigo",
        valor_original=1000.0,
        taxa_juros_mensal=0.0,
        parcelas_totais=10,
        parcelas_pagas=4,
        valor_parcela=100.0,
    )
    # 6 parcelas de 100 = 600
    assert debt.calculate_current_balance() == 600.0


def test_debt_balance_calculation_with_interest():
    """Testa cálculo de saldo com juros (Valor Presente)."""
    debt = Debt(
        nome="Financiamento",
        valor_original=5000.0,
        taxa_juros_mensal=2.0,
        parcelas_totais=12,
        parcelas_pagas=0,
        valor_parcela=500.0,
    )
    balance = debt.calculate_current_balance()
    # Com juros, o PV é menor que a soma bruta das parcelas (12 * 500 = 6000)
    assert balance < 6000.0
    assert balance > 5000.0  # Aproximadamente o valor original


def test_debt_mark_paid():
    """Testa o fluxo de pagamento de parcela."""
    debt = Debt(
        nome="Teste",
        valor_original=1000.0,
        taxa_juros_mensal=0.0,
        parcelas_totais=10,
        parcelas_pagas=0,
        valor_parcela=100.0,
    )
    debt.mark_installment_paid()
    assert debt.parcelas_pagas == 1
    assert debt.saldo_devedor_atual == 900.0


def test_insight_status_transition():
    """Testa transição de status do insight."""
    insight = Insight(
        type="Alerta", title="Gasto Alto", details="Você gastou muito em lazer."
    )
    assert insight.status == "Novo"
    insight.mark_as_read()
    assert insight.status == "Lido"
