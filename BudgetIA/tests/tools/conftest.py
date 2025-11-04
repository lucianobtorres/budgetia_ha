# Em: tests/tools/conftest.py
import pandas as pd
import pytest

import config
from finance.excel_handler import ExcelHandler
from finance.financial_calculator import FinancialCalculator
from finance.planilha_manager import PlanilhaManager


@pytest.fixture
def plan_manager_para_ferramentas() -> PlanilhaManager:
    """
    Cria um PlanilhaManager "dummy" em memória para os testes das ferramentas.
    Esta fixture estará disponível para TODOS os testes dentro da pasta /tools.
    """
    # Usamos um handler dummy que não lê/escreve arquivos reais
    handler_teste = ExcelHandler(file_path="dummy_tool_test.xlsx")

    # Suprimimos a lógica de inicialização padrão (load_sheets)
    # para ter um controle limpo
    class MockPlanilhaManager(PlanilhaManager):
        def __init__(self, excel_handler: ExcelHandler) -> None:
            self.excel_handler = excel_handler
            self.calculator = FinancialCalculator()
            # Inicializamos com DataFrames vazios definidos pelo layout
            self.dfs = {
                aba: pd.DataFrame(columns=colunas)
                for aba, colunas in config.LAYOUT_PLANILHA.items()
            }

    # Instanciamos nosso manager mockado
    plan_manager = MockPlanilhaManager(excel_handler=handler_teste)
    return plan_manager
