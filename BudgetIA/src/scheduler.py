# src/scheduler.py
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule

import config
from core.llm_enums import LLMProviderType
from core.llm_factory import LLMProviderFactory
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService

# 1. Encontra o diretório 'src' onde este arquivo está.
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Encontra a raiz do projeto (um nível acima do 'src').
PROJECT_ROOT = os.path.dirname(SRC_DIR)

# 3. Adiciona a RAIZ do projeto ao sys.path.
# Isso permite imports como 'from src.core import ...'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 4. Adiciona o PRÓPRIO 'src' ao sys.path.
# Isso permite imports como 'from core import ...' (embora o 'from src.core' seja mais explícito)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

print(f"--- DEBUG: SYS.PATH ATUALIZADO (para {__file__}) ---")
print(f"ROOT: {PROJECT_ROOT}")
print(f"SRC: {SRC_DIR}")
print("--- INICIANDO IMPORTS DA APLICAÇÃO ---")

from app import proactive_jobs  # Importa nossa lógica de job

print("--- SERVIÇO DE AGENDAMENTO (Scheduler) ---")
print("Inicializando...")

try:
    print("SCHEDULER: Criando LLMOrchestrator global...")
    # Usa Factory Pattern para consistência com resto do codebase
    primary_provider = LLMProviderFactory.create_provider(
        provider_type=LLMProviderType.GEMINI, default_model=config.DEFAULT_GEMINI_MODEL
    )
    LLM_ORCHESTRATOR = LLMOrchestrator(primary_provider=primary_provider)
except Exception as e:
    print(f"ERRO FATAL: Falha ao criar LLM Orchestrator. {e}")
    sys.exit(1)


def run_proactive_jobs_for_all_users() -> None:
    """
    Varre a pasta de usuários e dispara os jobs para cada um.
    """
    print(f"\n--- SCHEDULER: Verificando jobs para {datetime.now()} ---")

    users_dir = Path(os.path.join(config.DATA_DIR, "users"))
    if not users_dir.exists():
        print("SCHEDULER: Pasta 'data/users' não encontrada. Pulando.")
        return

    # Itera sobre cada pasta de usuário (ex: 'jsmith', 'mjane')
    for user_dir in users_dir.iterdir():
        if user_dir.is_dir():
            username = user_dir.name
            try:
                print(f"--- Processando jobs para o usuário: {username} ---")

                # Cria o serviço de config para este usuário
                config_service = UserConfigService(username)

                # --- 3. CHAMA O JOB (O "Trabalhador") ---
                # Injeta as dependências que o job precisa
                proactive_jobs.check_missing_daily_transport(
                    config_service=config_service, llm_orchestrator=LLM_ORCHESTRATOR
                )

                # (No futuro, você adicionaria mais jobs aqui)
                # proactive_jobs.check_upcoming_bills(config_service, LLM_ORCHESTRATOR)

            except Exception as e:
                print(f"ERRO SCHEDULER: Falha ao processar jobs para {username}: {e}")


# Para testar, vamos rodar a cada 1 minuto
print("Agendando 'check_missing_daily_transport' para rodar a cada 1 minuto.")
schedule.every(1).minutes.do(run_proactive_jobs_for_all_users)

print("Jobs agendados. Aguardando para executar...")


# --- Loop Principal ---
try:
    while True:
        schedule.run_pending()
        time.sleep(1)  # Dorme por 1 segundo para não fritar a CPU
except KeyboardInterrupt:
    print("\nEncerrando o agendador...")
