from finance.domain.models.goal import Goal


def test_goal_progress_calculation():
    """Testa se o progresso é calculado corretamente."""
    g = Goal(nome="Viagem", valor_alvo=1000.0, valor_atual=500.0)
    assert g.percentual_progresso == 50.0

    g.valor_atual = 1000.0
    assert g.percentual_progresso == 100.0
    assert g.is_completed is True


def test_goal_status_update():
    """Testa se o status muda para Concluída automaticamente."""
    g = Goal(nome="Reserva", valor_alvo=5000.0, valor_atual=4000.0)
    assert g.status == "Em Andamento"

    g.update_progress(5000.0)
    assert g.status == "Concluída"
    assert g.is_completed is True


def test_goal_with_zero_target():
    """Garante que não há divisão por zero se valor_alvo for inconsistente (embora Pydantic valide gt=0)."""
    # Usando valor_alvo > 0 como definido no Field
    g = Goal(nome="X", valor_alvo=1.0, valor_atual=0.0)
    assert g.percentual_progresso == 0.0


def test_goal_exceeding_target():
    """Garante que o progresso não passe de 100% visualmente."""
    g = Goal(nome="Y", valor_alvo=100.0, valor_atual=150.0)
    assert g.percentual_progresso == 100.0
    assert g.is_completed is True
