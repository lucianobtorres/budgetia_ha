
import os
import sys

# Setup Path
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from src.core.user_config_service import UserConfigService
from src.finance.factory import FinancialSystemFactory
from src.finance.storage.excel_storage_handler import ExcelHandler
from src.agent_implementations.factory import AgentFactory
from src.core.llm_manager import LLMOrchestrator
from src.core.llm_factory import LLMProviderFactory
from src.core.llm_enums import LLMProviderType
import config

# Clean start
TEST_USER = "memory_test_user"
config_service = UserConfigService(TEST_USER)
user_dir = config_service.get_user_dir()

print(f"--- TESTE MEMÓRIA: Usuário {TEST_USER} (Dir: {user_dir}) ---")

# Mock Spreadsheet
dummy_file = os.path.join(user_dir, "test_sheet.xlsx")
import pandas as pd
from config import LAYOUT_PLANILHA

# FORCE OVERWRITE
with pd.ExcelWriter(dummy_file, engine='openpyxl') as writer:
    for sheet_name, columns in LAYOUT_PLANILHA.items():
        pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet_name, index=False)

config_service.save_planilha_path(dummy_file)
path = config_service.get_planilha_path()
storage = ExcelHandler(path)

# Create Manager (Factory)
manager = FinancialSystemFactory.create_manager(
    storage_handler=storage,
    config_service=config_service
)

# Init LLM (Using Real API Key if available, else standard fallback)
# We assume the user has a valid key in .env or this will fail
try:
    provider = LLMProviderFactory.create_provider(LLMProviderType.GEMINI, default_model=config.DEFAULT_GEMINI_MODEL)
    orchestrator = LLMOrchestrator(provider)
except Exception as e:
    print(f"Skipping LLM init (API Key missing?): {e}")
    sys.exit(0)

# Create Agent (Factory)
agent_runner = AgentFactory.create_agent(
    llm_orchestrator=orchestrator,
    plan_manager=manager,
    config_service=config_service
)

print("\n\n--- 1. TESTE: Ensinar uma Preferência (LearnFactTool) ---")
response = agent_runner.interagir("Meu nome é Tester e eu adoro comer Sushi.")
print(f"RESPOSTA AGENTE: {response}")

# Verify via Service directly
from src.core.memory.memory_service import MemoryService
mem_service = MemoryService(user_dir)
facts = mem_service.search_facts("Sushi")
if facts:
    print(f"SUCCESS: Fato encontrado na memória: {facts[0]['content']}")
else:
    print("FAILURE: Fato não encontrado na memória.")

print("\n\n--- 2. TESTE: Recuperar Fato (Contexto/Search) ---")
# Clear agent memory (short term) to force using long term context
agent_runner.memory.clear()

response2 = agent_runner.interagir("O que eu gosto de comer?")
print(f"RESPOSTA AGENTE: {response2}")

if "ushi" in response2:
    print("SUCCESS: Agente lembrou do Sushi.")
else:
    print("FAILURE: Agente esqueceu do Sushi.")

print("\n\n--- 3. TESTE: Esquecer Fato (ForgetFactTool) ---")
response3 = agent_runner.interagir("Esqueça que eu gosto de Sushi.")
print(f"RESPOSTA AGENTE: {response3}")

facts_after = mem_service.search_facts("Sushi")
if not facts_after:
    print("SUCCESS: Fato removido da memória.")
else:
    print("FAILURE: Fato ainda existe.")
