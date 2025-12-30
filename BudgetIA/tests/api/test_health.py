from fastapi.testclient import TestClient
from interfaces.api.main import app

client = TestClient(app)

from unittest.mock import MagicMock
from interfaces.api.dependencies import get_planilha_manager
from finance.planilha_manager import PlanilhaManager

def test_health_check_returns_200():
    """Testa se o endpoint /health retorna status 200 e json correto."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "BudgetIA API"}

def test_readiness_check_structure():
    """Testa se o endpoint /readiness retorna a estrutura esperada."""
    
    # Mock do PlanilhaManager
    mock_manager = MagicMock(spec=PlanilhaManager)
    mock_manager.check_connection.return_value = (True, "Conectado")
    
    # Override da dependência
    app.dependency_overrides[get_planilha_manager] = lambda: mock_manager
    
    try:
        response = client.get("/api/readiness")
        
        # O status code esperado é 200 (OK)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "details" in data
        
    finally:
        # Limpa o override
        app.dependency_overrides = {}

