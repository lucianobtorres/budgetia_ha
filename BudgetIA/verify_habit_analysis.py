
import os
import sys
import pandas as pd
import asyncio
from unittest.mock import MagicMock 
import traceback # IMPORT TRACEBACK

# Setup Path
sys.path.insert(0, os.getcwd())

try:
    from dotenv import load_dotenv
    load_dotenv()

    from src.core.user_config_service import UserConfigService
    from src.finance.factory import FinancialSystemFactory
    from src.finance.storage.excel_storage_handler import ExcelHandler
    from src.agent_implementations.factory import AgentFactory
    from src.core.llm_manager import LLMOrchestrator
    from src.core.llm_factory import LLMProviderFactory
    from src.core.llm_enums import LLMProviderType
    from src.core.memory.memory_service import MemoryService
    import config
    from config import LAYOUT_PLANILHA

    # Clean start
    TEST_USER = "observer_test_user_v2"
    config_service = UserConfigService(TEST_USER)
    user_dir = config_service.get_user_dir()
    memory_service = MemoryService(user_dir)

    print(f"--- TESTE OBSERVADOR (MOCKED): Usuário {TEST_USER} ---")
    if os.path.exists(os.path.join(user_dir, "memory.json")):
        os.remove(os.path.join(user_dir, "memory.json"))

    # Mock Spreadsheet
    dummy_file = os.path.join(user_dir, "test_sheet_observer_mock.xlsx")
    with pd.ExcelWriter(dummy_file, engine='openpyxl') as writer:
        for sheet_name, columns in LAYOUT_PLANILHA.items():
            pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet_name, index=False)

    config_service.save_planilha_path(dummy_file)
    path = config_service.get_planilha_path()
    storage = ExcelHandler(path)

    manager = FinancialSystemFactory.create_manager(
        storage_handler=storage,
        config_service=config_service
    )

    # SEED
    for i in range(4):
        manager.adicionar_registro(
            data="18/12/2025",
            tipo="Despesa",
            categoria="Alimentação",
            descricao="Ifood",
            valor=85.50
        )

    # INIT LLM
    provider = LLMProviderFactory.create_provider(LLMProviderType.GEMINI, default_model=config.DEFAULT_GEMINI_MODEL)
    orchestrator = LLMOrchestrator(provider)

    # --- MOCK ---
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"facts": ["Usuário gasta frequentemente com Ifood (R$ 85.50)."]}'
    mock_llm.invoke.return_value = mock_response

    # HACK: Force mocked LLM
    orchestrator.get_configured_llm = MagicMock(return_value=mock_llm)
    orchestrator.get_current_llm = MagicMock(return_value=mock_llm)

    # Component Test
    from src.app.services.behavior_analyst import BehaviorAnalyst
    print(">> Testando Componente BehaviorAnalyst isolado...")
    analyst = BehaviorAnalyst(orchestrator, memory_service)
    
    # Get Data
    df = manager.visualizar_dados("Visão Geral e Transações")
    print(f"Dados para análise: {len(df)} linhas.")

    # RUN
    facts = analyst.analyze_recent_transactions(df)
    print(f"Fatos retornados pelo Analyst (Mocked): {facts}")

    print("\n\n--- VERIFICAÇÃO FINAL: Memória ---")
    mem_facts = memory_service.search_facts("Ifood")
    print(f"Memória Persistida: {mem_facts}")

    if "Ifood" in str(mem_facts):
        print("SUCCESS: O Analyst gravou corretamente na memória.")
    else:
        print("FAILURE: Fatos não encontrados.")

except Exception:
    with open("error_log.txt", "w") as f:
        traceback.print_exc(file=f)
    traceback.print_exc()
    sys.exit(1)
