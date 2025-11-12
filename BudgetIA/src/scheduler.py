# src/scheduler.py
import os
import sys
import time

import schedule

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

# --- Configuração dos Jobs ---

# Para testar, vamos rodar a cada 1 minuto
print("Agendando 'check_missing_daily_transport' para rodar a cada 1 minuto.")
schedule.every(1).minutes.do(proactive_jobs.check_missing_daily_transport)

# (No futuro, você pode mudar para isso)
# schedule.every().day.at("20:00").do(proactive_jobs.check_missing_daily_transport)

print("Jobs agendados. Aguardando para executar...")

# --- Loop Principal ---
try:
    while True:
        schedule.run_pending()
        time.sleep(1)  # Dorme por 1 segundo para não fritar a CPU
except KeyboardInterrupt:
    print("\nEncerrando o agendador...")
