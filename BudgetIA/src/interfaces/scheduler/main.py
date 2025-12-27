# src/scheduler.py
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule

import config


# 1. Encontra o diretório onde este arquivo está (src/scheduler)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Encontra o diretório 'src' (um nível acima)
SRC_DIR = os.path.dirname(CURRENT_DIR)

# 3. Encontra a raiz do projeto (um nível acima do 'src')
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

print("--- SERVIÇO DE AGENDAMENTO (Scheduler - API Client) ---")

# Importa o cliente da API
from interfaces.web_app.api_client import BudgetAPIClient

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def run_proactive_jobs_for_all_users() -> None:
    """
    Varre a pasta de usuários e dispara os jobs via API para cada um.
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
            
            # Pula usuários de sistema/teste
            if username == "default_user":
                continue

            # Verifica se tem config básico
            config_file = user_dir / "user_config.json"
            if not config_file.exists():
                print(f"SCHEDULER: Usuário '{username}' sem config. Pulando.")
                continue

            try:
                print(f"--- Disparando job via API para: {username} ---")
                
                # Instancia cliente personificado
                client = BudgetAPIClient(base_url=API_URL, user_id=username)
                
                # Dispara job
                result = client.trigger_proactive_job()
                print(f"SCHEDULER Result ({username}): {result}")

            except Exception as e:
                print(f"ERRO SCHEDULER: Falha ao processar jobs para {username}: {e}")


# Para testar, vamos rodar a cada 1 minuto
print("Agendando jobs para rodar a cada 1 minuto.")
schedule.every(1).minutes.do(run_proactive_jobs_for_all_users)

print("Jobs agendados. Aguardando para executar...")


# --- Loop Principal ---
try:
    while True:
        schedule.run_pending()
        time.sleep(1)  # Dorme por 1 segundo para não fritar a CPU
except KeyboardInterrupt:
    print("\nEncerrando o agendador...")
