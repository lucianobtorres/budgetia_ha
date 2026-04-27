from finance.domain.models.budget import Budget


def test_budget_creation_valid():
    """Testa a criação de um orçamento válido."""
    b = Budget(categoria="Alimentação", limite=1000.0, gasto_atual=250.0)
    assert b.categoria == "Alimentação"
    assert b.limite == 1000.0
    assert b.gasto_atual == 250.0


def test_budget_percentage_calculation():
    """Testa se o percentual de gasto é calculado corretamente."""
    b = Budget(categoria="Lazer", limite=500.0, gasto_atual=250.0)
    assert b.percentual_gasto == 50.0

    # Caso limite zero para evitar divisão por zero
    b_zero = Budget(categoria="X", limite=0.0, gasto_atual=100.0)
    assert b_zero.percentual_gasto == 100.0  # Se não tem limite, gastou 100% ou mais


def test_budget_status_logic():
    """Testa a lógica de status baseada no gasto."""
    # OK
    b_ok = Budget(categoria="A", limite=100.0, gasto_atual=50.0)
    assert b_ok.status == "OK"

    # Atenção (> 80%)
    b_warn = Budget(categoria="B", limite=100.0, gasto_atual=85.0)
    assert b_warn.status == "Atenção"

    # Excedido (> 100%)
    b_exceeded = Budget(categoria="C", limite=100.0, gasto_atual=110.0)
    assert b_exceeded.status == "Excedido"


def test_budget_is_over_limit():
    """Testa o helper de limite excedido."""
    b = Budget(categoria="D", limite=100.0, gasto_atual=101.0)
    assert b.is_over_limit is True
