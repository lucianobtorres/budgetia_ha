from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from finance.planilha_manager import PlanilhaManager
from interfaces.api.dependencies import get_planilha_manager
from interfaces.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_manager():
    manager = MagicMock(spec=PlanilhaManager)
    app.dependency_overrides[get_planilha_manager] = lambda: manager
    yield manager
    app.dependency_overrides = {}


def test_list_categories(mock_manager):
    """Testa listagem de categorias."""
    # Mock de dados internos da planilha de categorias
    mock_df = pd.DataFrame(
        [
            {
                "Nome": "Alimentação",
                "Tipo (Despesa/Receita)": "Despesa",
                "Icone": "Coffee",
                "Palavras-Chave": "comida,restaurante",
            },
            {
                "Nome": "Salário",
                "Tipo (Despesa/Receita)": "Receita",
                "Icone": "Dollar",
                "Palavras-Chave": "pagamento",
            },
        ]
    )
    mock_manager.get_categorias.return_value = mock_df

    response = client.get("/api/categories/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Alimentação"
    assert data[1]["type"] == "Receita"
