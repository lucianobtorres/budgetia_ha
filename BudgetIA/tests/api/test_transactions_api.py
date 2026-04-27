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
    manager.list_transactions_use_case = MagicMock()
    manager.add_transaction_use_case = MagicMock()

    app.dependency_overrides[get_planilha_manager] = lambda: manager
    yield manager
    app.dependency_overrides = {}


def test_listar_transacoes_vazio(mock_manager):
    """Testa listagem de transações quando a planilha está vazia."""
    mock_manager.list_transactions_use_case.execute.return_value = []
    response = client.get("/api/transactions/")
    assert response.status_code == 200
    assert response.json() == []


def test_adicionar_transacao_valida(mock_manager):
    """Testa a adição de uma transação válida."""
    payload = {
        "data": "2024-01-01",
        "tipo": "Despesa",
        "categoria": "Alimentação",
        "descricao": "Pão de sal",
        "valor": 5.50,
        "status": "Concluído",
        "parcelas": 1,
    }
    response = client.post("/api/transactions/", json=payload)
    print("RESPONSE JSON:", response.json())
    assert response.status_code == 200
    assert "message" in response.json()
    mock_manager.add_transaction_use_case.execute.assert_called_once()


def test_adicionar_transacao_invalida(mock_manager):
    """Testa se a API rejeita dados inválidos (ex: valor como string)."""
    payload = {
        "tipo": "Despesa",
        "categoria": "Alimentação",
        "descricao": "Erro",
        "valor": "muito caro",  # Erro aqui: deve ser número
        "status": "Concluído",
    }
    response = client.post("/api/transactions/", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
