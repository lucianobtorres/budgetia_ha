# Em: tests/tools/conftest.py
from unittest.mock import MagicMock

import pandas as pd
import pytest

import config
from finance.excel_handler import ExcelHandler
from finance.financial_calculator import FinancialCalculator
from finance.planilha_manager import PlanilhaManager

# --- NOVO IMPORT ---
from finance.repositories.budget_repository import BudgetRepository
from finance.repositories.data_context import FinancialDataContext
from finance.repositories.debt_repository import DebtRepository
from finance.repositories.insight_repository import InsightRepository
from finance.repositories.profile_repository import ProfileRepository
from finance.repositories.transaction_repository import TransactionRepository


@pytest.fixture
def plan_manager_para_ferramentas() -> PlanilhaManager:
    """
    Cria um PlanilhaManager "dummy" em memória para os testes das ferramentas.
    Simula a nova estrutura interna com todos os repositórios reais.
    """

    # 1. Mockar o ExcelHandler
    handler_teste = MagicMock(spec=ExcelHandler)
    handler_teste.file_path = "dummy_tool_test.xlsx"
    mock_dfs = {
        aba: pd.DataFrame(columns=colunas)
        for aba, colunas in config.LAYOUT_PLANILHA.items()
    }
    handler_teste.load_sheets.return_value = (mock_dfs, True)  # is_new_file

    # 2. Criar Componentes Reais
    data_context_real = FinancialDataContext(
        excel_handler=handler_teste, mapeamento=None
    )
    data_context_real.save = MagicMock()  # Mocka o save

    calculator_real = FinancialCalculator()

    transaction_repo_real = TransactionRepository(
        context=data_context_real, calculator=calculator_real
    )

    budget_repo_real = BudgetRepository(
        context=data_context_real,
        calculator=calculator_real,
        transaction_repo=transaction_repo_real,
    )

    debt_repo_real = DebtRepository(
        context=data_context_real, calculator=calculator_real
    )

    profile_repo_real = ProfileRepository(context=data_context_real)

    # --- NOVO PASSO: Criar o InsightRepository REAL ---
    insight_repo_real = InsightRepository(context=data_context_real)
    # --- FIM DO NOVO PASSO ---

    # 3. Criar a classe PlanilhaManager (a fachada)
    plan_manager = PlanilhaManager.__new__(PlanilhaManager)

    # 4. Injetar manualmente os componentes
    plan_manager._context = data_context_real
    plan_manager.calculator = calculator_real
    plan_manager.transaction_repo = transaction_repo_real
    plan_manager.budget_repo = budget_repo_real
    plan_manager.debt_repo = debt_repo_real
    plan_manager.profile_repo = profile_repo_real
    plan_manager.insight_repo = insight_repo_real  # Injeta o novo repo
    plan_manager.is_new_file = True

    # 5. Mockar os métodos de orquestração
    plan_manager.save = data_context_real.save
    plan_manager.recalculate_budgets = MagicMock()

    # Os métodos reais (adicionar_insight_ia, etc.)
    # agora delegam para o repo real injetado.

    return plan_manager
