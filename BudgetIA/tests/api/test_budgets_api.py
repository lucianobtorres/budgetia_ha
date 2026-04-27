from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from finance.planilha_manager import PlanilhaManager
from interfaces.api.dependencies import get_planilha_manager
from interfaces.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_manager():
    manager = MagicMock(spec=PlanilhaManager)
    manager.lock_file.return_value.__enter__.return_value = None
    manager.list_budgets_use_case = MagicMock()
    manager.define_budget_use_case = MagicMock()

    app.dependency_overrides[get_planilha_manager] = lambda: manager
    yield manager
    app.dependency_overrides = {}


def test_listar_orcamentos_vazio(mock_manager):
    """Testa listagem de orçamentos vazia."""
    mock_manager.list_budgets_use_case.execute.return_value = []
    response = client.get("/api/budgets/")
    assert response.status_code == 200
    assert response.json() == []


def test_add_orcamento_valido(mock_manager):
    """Testa adicionar um novo orçamento."""
    mock_manager.adicionar_ou_atualizar_orcamento.return_value = (
        "Orçamento criado com sucesso."
    )
    payload = {
        "categoria": "Lazer",
        "valor_limite": 500.0,
        "periodo": "Mensal",
        "observacoes": "Cinema e tal",
    }
    response = client.post("/api/budgets/", json=payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Orçamento criado com sucesso."}


def test_add_orcamento_invalido(mock_manager):
    """Testa se a API valida campos obrigatórios."""
    payload = {
        "valor_limite": 500.0  # Falta categoria
    }
    response = client.post("/api/budgets/", json=payload)
    assert response.status_code == 422
