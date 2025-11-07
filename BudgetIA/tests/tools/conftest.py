# Em: tests/tools/conftest.py

from typing import Any

import pandas as pd
import pytest

# Importações do projeto
import config
from finance.excel_handler import ExcelHandler
from finance.financial_calculator import FinancialCalculator
from finance.planilha_manager import PlanilhaManager

# --- NOVA IMPORTAÇÃO ---
# Precisamos das estratégias para criar um mock real
from finance.strategies.base_strategy import BaseMappingStrategy
from finance.strategies.default_strategy import DefaultStrategy

# --- FIM DA NOVA IMPORTAÇÃO ---


@pytest.fixture
def plan_manager_para_ferramentas() -> PlanilhaManager:
    """
    Fixture que cria um PlanilhaManager "Mock" na memória para testes
    de ferramentas.
    - Evita I/O de disco (não lê/salva arquivos).
    - Fornece um ambiente limpo (self.dfs) para cada teste.
    """

    class MockPlanilhaManager(PlanilhaManager):
        """Mock que herda do real, mas sobrescreve I/O."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            # Não chama o __init__ pai para evitar I/O
            self.dfs = {
                aba: pd.DataFrame(columns=cols)
                for aba, cols in config.LAYOUT_PLANILHA.items()
            }
            self.calculator = FinancialCalculator()
            self.is_new_file = True

            # --- CORREÇÃO: Adiciona o atributo 'strategy' ---
            # O mock agora se parece mais com o objeto real
            # Usamos a DefaultStrategy, pois é a mais simples
            self.strategy: BaseMappingStrategy = DefaultStrategy(
                config.LAYOUT_PLANILHA, None
            )
            # --- FIM DA CORREÇÃO ---

            # (O excel_handler pode ser None, pois vamos sobrescrever o save)
            self.excel_handler: ExcelHandler | None = None

        def save(self, add_intelligence: bool = False) -> None:
            """
            Sobrescreve (overrides) o método 'save' real.
            Em vez de salvar no disco, ele apenas "finge".

            Como este método agora usa 'self.strategy' no código real,
            o nosso mock DEVE ter 'self.strategy' (adicionado acima)
            para que a assinatura da herança seja válida, mesmo que
            não o usemos aqui.
            """
            # Simula o salvamento, mas não faz nada
            print("--- MOCK SAVE CALLED (sem I/O) ---")
            pass

    # Instancia o Mock
    # Passamos excel_handler=None pois o __init__ real não será chamado
    # e o método save() (que o usa) está mockado.
    return MockPlanilhaManager(excel_handler=None, mapeamento=None)
