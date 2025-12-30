# tests/conftest.py
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from core.user_config_service import UserConfigService
from finance.factory import FinancialSystemFactory
from finance.planilha_manager import PlanilhaManager
from finance.storage.base_storage_handler import BaseStorageHandler

# --- INÍCIO DA CORREÇÃO: Adicionar a Raiz do Projeto ao sys.path ---

# 1. Encontra o caminho para este arquivo (conftest.py)
CURRENT_DIR = Path(__file__).parent

# 2. Encontra a Raiz do Projeto (um nível acima da pasta 'tests')
PROJECT_ROOT = CURRENT_DIR.parent

# 3. Adiciona a Raiz do Projeto (ex: C:\...BudgetIA\BudgetIA) ao sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 4. Adiciona a pasta 'src' ao sys.path para suportar imports diretos (ex: 'from config import ...')
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Agora, o Python saberá onde encontrar a pasta 'src'
# e tanto 'import src.core...' quanto 'import config...' funcionarão.
print(f"--- DEBUG conftest.py: Adicionado '{PROJECT_ROOT}' e '{SRC_DIR}' ao sys.path ---")

TEST_ENCRYPTION_KEY = Fernet.generate_key()


@pytest.fixture
def mock_storage_handler() -> MagicMock:
    """Cria um mock genérico do BaseStorageHandler."""
    # (Usamos 'autospec=True' para garantir que ele só tenha
    # métodos que a interface real tem)
    handler = MagicMock(spec=BaseStorageHandler)
    handler.resource_id = "test_resource_id"

    # --- CORREÇÃO: Retornar DFs vazios, mas inicializados ---
    import pandas as pd
    from config import LAYOUT_PLANILHA

    mock_dfs = {
        aba: pd.DataFrame(columns=colunas)
        for aba, colunas in LAYOUT_PLANILHA.items()
    }

    # Define valores de retorno padrão para o 'load_sheets'
    # (dados vazios, não é um arquivo novo)
    handler.load_sheets.return_value = (mock_dfs, False)
    return handler


@pytest.fixture
def plan_manager_para_ferramentas(
    mock_storage_handler: MagicMock,
) -> PlanilhaManager:
    """Fixture do PlanilhaManager para injetar nas ferramentas."""

    # Cria um mock do UserConfigService
    mock_config_service = MagicMock(spec=UserConfigService)
    mock_config_service.username = "tool_test_user"
    mock_config_service.get_mapeamento.return_value = None

    # Pula o 'recalculate_budgets'
    # Pula o 'recalculate_budgets' e evita Redis real
    with patch.object(PlanilhaManager, "recalculate_budgets", return_value=None), \
         patch("finance.factory.RedisCacheService") as mock_redis_service:
        
        # Configura o mock do Redis para evitar erros
        mock_instance = mock_redis_service.return_value
        mock_instance.get_entry.return_value = (None, None)
        mock_instance.set_entry.return_value = True

        plan_manager = FinancialSystemFactory.create_manager(
            storage_handler=mock_storage_handler,
            config_service=mock_config_service,
        )
    return plan_manager


@pytest.fixture(autouse=True)
def mock_env_and_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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
