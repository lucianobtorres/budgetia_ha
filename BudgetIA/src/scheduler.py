# src/scheduler.py
import os
import sys
import time

import schedule

# Adiciona 'src' ao sys.path para que possamos importar 'app' e 'config'
# (Esta é a mágica que faz o backend ser reutilizável)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
