# Em tests/conftest.py (ou no topo do seu novo arquivo de teste)
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

# --- 1. A Chave de Teste ---
# Geramos uma chave válida que será usada APENAS para estes testes.
TEST_ENCRYPTION_KEY = Fernet.generate_key()


@pytest.fixture(autouse=True)
def mock_env_and_config(monkeypatch, tmp_path: Path) -> None:
    """
    Fixture principal. Roda automaticamente para cada teste.
    - 'monkeypatch' altera variáveis de ambiente e globais.
    - 'tmp_path' fornece um diretório temporário limpo para cada teste.
    """

    # --- 2. Mock da Variável de Ambiente ---
    # "Engana" o os.getenv("USER_DATA_ENCRYPTION_KEY")
    monkeypatch.setenv("USER_DATA_ENCRYPTION_KEY", TEST_ENCRYPTION_KEY.decode("utf-8"))

    # --- 3. Mock do Módulo 'config' ---
    # "Engana" o 'config.DATA_DIR' para apontar para nossa pasta temporária
    monkeypatch.setattr("config.DATA_DIR", tmp_path)

    # --- 4. Mock do Módulo 'user_config_service' ---
    # Recarrega o módulo 'user_config_service' para que ele leia
    # a variável de ambiente que acabamos de mockar.
    import src.core.user_config_service as config_service_module

    config_service_module.ENCRYPTION_KEY = TEST_ENCRYPTION_KEY
    config_service_module.FERNET = Fernet(TEST_ENCRYPTION_KEY)

    # Permite que o teste prossiga
    yield
