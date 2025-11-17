# tests/conftest.py
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from cryptography.fernet import Fernet

import config
from core.user_config_service import UserConfigService
from finance.planilha_manager import PlanilhaManager
from finance.repositories.data_context import FinancialDataContext
from finance.storage.excel_storage_handler import ExcelHandler

# --- INÍCIO DA CORREÇÃO: Adicionar a Raiz do Projeto ao sys.path ---

# 1. Encontra o caminho para este arquivo (conftest.py)
CURRENT_DIR = Path(__file__).parent

# 2. Encontra a Raiz do Projeto (um nível acima da pasta 'tests')
PROJECT_ROOT = CURRENT_DIR.parent

# 3. Adiciona a Raiz do Projeto (ex: C:\...BudgetIA\BudgetIA) ao sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Agora, o Python saberá onde encontrar a pasta 'src'
# e o import 'from src.core...' funcionará.
print(f"--- DEBUG conftest.py: Adicionado '{PROJECT_ROOT}' ao sys.path ---")

TEST_ENCRYPTION_KEY = Fernet.generate_key()


@pytest.fixture
def plan_manager_para_ferramentas() -> PlanilhaManager:
    """
    Cria um PlanilhaManager "dummy" em memória para os testes das ferramentas.
    Simula a nova estrutura interna com todos os repositórios reais.
    """

    # 1. Mockar o ExcelHandler (como antes)
    handler_teste = MagicMock(spec=ExcelHandler)
    handler_teste.file_path = "dummy_tool_test.xlsx"
    mock_dfs = {
        aba: pd.DataFrame(columns=colunas)
        for aba, colunas in config.LAYOUT_PLANILHA.items()
    }
    # Força o caminho de "novo arquivo" no PlanilhaManager
    handler_teste.load_sheets.return_value = (mock_dfs, True)

    # 2. Mockar o ConfigService (para isolar o teste)
    mock_config_service = MagicMock(spec=UserConfigService)
    # Garante que ele não vai tentar carregar uma estratégia customizada
    mock_config_service.get_mapeamento.return_value = None

    # 3. Pular a lógica de 'populate' e 'save' no __init__
    # para ter um ambiente 100% limpo e controlado
    with (
        patch.object(PlanilhaManager, "_populate_initial_data", return_value=None),
        patch.object(FinancialDataContext, "save", return_value=None),
    ):
        # 4. Criar o PlanilhaManager real, que vai construir
        # seus próprios componentes internos
        plan_manager = PlanilhaManager(
            storage_handler=handler_teste, config_service=mock_config_service
        )

    # 5. Mockar métodos de alto nível para isolar as ferramentas
    plan_manager.save = MagicMock()
    plan_manager.recalculate_budgets = MagicMock()

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
