from fastapi.testclient import TestClient
from interfaces.api.main import app

client = TestClient(app)

def test_health_check_returns_200():
    """Testa se o endpoint /health retorna status 200 e json correto."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "BudgetIA API"}

def test_readiness_check_structure():
    """Testa se o endpoint /readiness retorna a estrutura esperada (mesmo que haja erro de conexão)."""
    response = client.get("/readiness")
    # O status code pode ser 200 (OK) ou 503 (Service Unavailable - se não configurado)
    assert response.status_code in [200, 503]
    data = response.json()
    
    if response.status_code == 503:
        # Se for erro de serviço indisponível (HTTPException), o FastAPI retorna 'detail'
        assert "detail" in data
    else:
        # Se for sucesso (ou erro tratado dentro da função), retorna o nosso schema
        assert "status" in data
        assert "details" in data
        assert data["status"] in ["ready", "error"]
