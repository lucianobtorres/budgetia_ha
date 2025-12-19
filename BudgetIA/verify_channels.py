
import os
import sys
import asyncio
import pandas as pd
from datetime import datetime

# Setup Path
sys.path.insert(0, os.getcwd())

from src.core.user_config_service import UserConfigService
from src.app.notifications.orchestrator import ProactiveNotificationOrchestrator
from src.app.notifications.channels.whatsapp_channel import WhatsAppChannel
from src.app.notifications.channels.email_channel import EmailChannel
from src.app.notifications.rules.dynamic_rule import DynamicThresholdRule
from src.finance.factory import FinancialSystemFactory
from src.finance.storage.excel_storage_handler import ExcelHandler
from config import LAYOUT_PLANILHA

# 1. Setup User & Config
TEST_USER = "channel_test_user"
config_service = UserConfigService(TEST_USER)
user_dir = config_service.get_user_dir()

print(f"--- TESTE CANAIS: Usuário {TEST_USER} ---")

# 2. Configurar Canais (Simular preenchimento na UI Conexões)
print("Configurando canais...")
config_service.save_comunicacao_field("whatsapp_phone", "+5511999998888")
config_service.save_comunicacao_field("email_address", "test@budgetia.com")
# Telegram não configurado para testar ausência

# 3. Setup Mock Spreadsheet
dummy_file = os.path.join(user_dir, "test_channels.xlsx")
with pd.ExcelWriter(dummy_file, engine='openpyxl') as writer:
    for sheet_name, columns in LAYOUT_PLANILHA.items():
        pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet_name, index=False)
config_service.save_planilha_path(dummy_file)
storage = ExcelHandler(dummy_file)
manager = FinancialSystemFactory.create_manager(storage, config_service)

# Adicionar transação que dispara regra
manager.adicionar_registro(
    data=datetime.now().strftime("%d/%m/%Y"),
    tipo="Despesa",
    categoria="Jogos",
    descricao="Steam Game",
    valor=200.00
)

# 4. Criar Regra que dispara (Threshold 50.00)
rule = DynamicThresholdRule(
    rule_id="test_rule_1",
    category="Jogos",
    threshold=50.00,
    period="monthly"
)

# 5. Criar Orchestrator
channels = [WhatsAppChannel(), EmailChannel()] # Injetar apenas os que queremos testar envio explícito
orchestrator = ProactiveNotificationOrchestrator(
    rules=[rule],
    channels=channels,
    config_service=config_service
)

# 6. Rodar
print("\n--- RODANDO ORCHESTRATOR ---")
async def main():
    result = await orchestrator.run(manager)
    print("Resultado:", result)

if __name__ == "__main__":
    asyncio.run(main())
