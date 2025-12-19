
import os
import sys
import pandas as pd
import asyncio

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
from config import LAYOUT_PLANILHA
from src.app.notifications.rule_repository import RuleRepository

# Clean start
TEST_USER = "rules_test_user_v2"
config_service = UserConfigService(TEST_USER)
user_dir = config_service.get_user_dir()

print(f"--- TESTE REGRAS: Usuário {TEST_USER} (Dir: {user_dir}) ---")
# CLEAN RULES FIRST
if os.path.exists(os.path.join(user_dir, "rules.json")):
    os.remove(os.path.join(user_dir, "rules.json"))

# Mock Spreadsheet
dummy_file = os.path.join(user_dir, "test_sheet_rules.xlsx")

# Force fresh sheet
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

# Init LLM
try:
    provider = LLMProviderFactory.create_provider(LLMProviderType.GEMINI, default_model=config.DEFAULT_GEMINI_MODEL)
    orchestrator = LLMOrchestrator(provider)
except Exception as e:
    print(f"Skipping LLM init (API Key missing?): {e}")
    sys.exit(0)

# Create Agent
agent_runner = AgentFactory.create_agent(
    llm_orchestrator=orchestrator,
    plan_manager=manager,
    config_service=config_service
)

print("\n\n--- 1. TESTE: Solicitar Criação de Regra MENSAL ---")
user_input = "Me avise se eu gastar mais de 100,00 reais com Pizza este Mês."
print(f"USUÁRIO: {user_input}")
response = agent_runner.interagir(user_input)
print(f"AGENTE: {response}")

repo = RuleRepository(user_dir)
rules_v1 = repo.get_all_rules()
print(f"Regras V1: {[r.rule_name for r in rules_v1]}")
assert any('pizza' in r.rule_name and 'monthly' in r.rule_name for r in rules_v1)

print("\n\n--- 2. TESTE: Mudar para SEMANAL (Deve substituir) ---")
user_input_2 = "Na verdade mude para 100 reais por SEMANA."
print(f"USUÁRIO: {user_input_2}")
response_2 = agent_runner.interagir(user_input_2)
print(f"AGENTE: {response_2}")

rules_v2 = repo.get_all_rules()
print(f"Regras V2: {[r.rule_name for r in rules_v2]}")

has_monthly = any('pizza' in r.rule_name and 'monthly' in r.rule_name for r in rules_v2)
has_weekly = any('pizza' in r.rule_name and 'weekly' in r.rule_name for r in rules_v2)

if not has_monthly and has_weekly:
    print("SUCCESS: A regra MENSAL foi removida e a SEMANAL foi criada.")
else:
    print(f"FAILURE: Estado incorreto. Mensal={has_monthly}, Semanal={has_weekly}")
    sys.exit(1)
