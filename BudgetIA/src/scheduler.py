# src/scheduler.py
import datetime
import os
import sys
import time

import schedule

import config
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider
from core.user_config_service import UserConfigService

# 1. Encontra o diretório 'src' onde este arquivo está.
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Encontra a raiz do projeto (um nível acima do 'src').
PROJECT_ROOT = os.path.dirname(SRC_DIR)

# 3. Adiciona a RAIZ do projeto ao sys.path.
# Isso permite imports como 'from src.core import ...'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
SCHEDULER_USERNAME = "jsmith"
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
    PRIMARY_PROVIDER = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
    LLM_ORCHESTRATOR = LLMOrchestrator(primary_provider=PRIMARY_PROVIDER)
except Exception as e:
    print(f"ERRO FATAL: Falha ao criar LLM Orchestrator. {e}")
    sys.exit(1)


def run_proactive_jobs_for_all_users():
    """
    Varre a pasta de usuários e dispara os jobs para cada um.
    """
    print(f"\n--- SCHEDULER: Verificando jobs para {datetime.now()} ---")

    users_dir = Path(config.DATA_DIR) / "users"
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
schedule.every(1).minutes.do(proactive_jobs.check_missing_daily_transport)

# (No futuro, você pode mudar para isso)
# schedule.every().day.at("20:00").do(proactive_jobs.check_missing_daily_transport)

print("Jobs agendados. Aguardando para executar...")


def run_job(job_func):
    """Wrapper para carregar o sistema e injetar nos jobs."""
    print(f"\n--- JOB PROATIVO: {datetime.now()} ---")
    try:
        # --- 2. INICIALIZAR OS SERVIÇOS ---
        print(f"SCHEDULER: Carregando sistema para '{SCHEDULER_USERNAME}'...")
        config_service = UserConfigService(SCHEDULER_USERNAME)

        primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
        llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)

        # --- 3. INJETAR SERVIÇOS NO JOB ---
        # (Assumindo que seus jobs em 'proactive_jobs'
        #  agora aceitam 'config_service' e 'llm_orchestrator')
        job_func(config_service=config_service, llm_orchestrator=llm_orchestrator)

    except Exception as e:
        print(f"ERRO JOB: {e}")


# --- Loop Principal ---
try:
    while True:
        schedule.run_pending()
        time.sleep(1)  # Dorme por 1 segundo para não fritar a CPU
except KeyboardInterrupt:
    print("\nEncerrando o agendador...")

if __name__ == "__main__":
    print("--- SERVIÇO DE AGENDAMENTO (Scheduler) ---")
    print("Inicializando...")

    # --- 4. ATUALIZAR A CHAMADA DO JOB ---
    # (Precisamos usar 'run_job' para injetar as dependências)
    schedule.every(1).minutes.do(run_job, proactive_jobs.check_missing_daily_transport)
    # ... (outros jobs) ...

    print("Jobs agendados. Aguardando para executar...")
    while True:
        schedule.run_pending()
        time.sleep(1)
