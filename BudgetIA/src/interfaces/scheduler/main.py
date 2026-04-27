# src/scheduler.py
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule

import config
from core.logger import get_logger

logger = get_logger("Scheduler")


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


logger.info("SERVIÇO DE AGENDAMENTO (Scheduler - API Client)")

import requests  # noqa: E402

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


def wait_for_api(url: str, timeout: int = 60) -> bool:
    """Aguarda a API ficar disponível."""
    start_time = time.time()
    logger.info(f"Aguardando API em {url} ficar pronta...")
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/api/health")
            if response.status_code == 200:
                logger.info("✅ API detectada e pronta!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    logger.error("❌ Timeout aguardando API.")
    return False


def run_proactive_jobs_for_all_users() -> None:
    """
    Varre a pasta de usuários e dispara os jobs via API para cada um.
    Restringe o envio para o horário comercial (09:00 - 21:00).
    """
    current_hour = datetime.now().hour
    if current_hour < 9 or current_hour >= 21:
        logger.debug(
            f"Fora do horário comercial ({current_hour}h). Pulando notificações."
        )
        return

    logger.info(f"Verificando jobs para {datetime.now()}")

    users_dir = Path(os.path.join(config.DATA_DIR, "users"))
    if not users_dir.exists():
        logger.warning("Pasta 'data/users' não encontrada. Pulando.")
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
                logger.info(f"Usuário '{username}' sem config. Pulando.")
                continue

            try:
                logger.info(f"Disparando job via API para: {username}")

                # Dispara job
                response = requests.post(
                    f"{API_URL}/api/jobs/run", headers={"X-User-ID": username}
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Result ({username}): {result}")

            except Exception as e:
                logger.error(f"Falha ao processar jobs para {username}: {e}")


def run_sanitize_jobs_for_all_users() -> None:
    """
    Varre a pasta de usuários e dispara a FAXINA via API para cada um.
    """
    logger.info("--- INICIANDO FAXINA DIÁRIA ---")
    users_dir = Path(os.path.join(config.DATA_DIR, "users"))
    if not users_dir.exists():
        return

    for user_dir in users_dir.iterdir():
        if user_dir.is_dir():
            username = user_dir.name
            if username == "default_user":
                continue

            try:
                logger.info(f"Disparando FAXINA para: {username}")
                response = requests.post(
                    f"{API_URL}/api/jobs/sanitize", headers={"X-User-ID": username}
                )
                response.raise_for_status()
                logger.info(f"Faxina Concluída ({username})")
            except Exception as e:
                logger.error(f"Falha na faxina de {username}: {e}")


def run_learning_jobs_for_all_users() -> None:
    """
    Varre a pasta de usuários e dispara o APRENDIZADO via API para cada um.
    """
    logger.info("--- INICIANDO APRENDIZADO DE COMPORTAMENTO ---")
    users_dir = Path(os.path.join(config.DATA_DIR, "users"))
    if not users_dir.exists():
        return

    for user_dir in users_dir.iterdir():
        if user_dir.is_dir():
            username = user_dir.name
            if username == "default_user":
                continue

            try:
                logger.info(f"Disparando APRENDIZADO para: {username}")
                response = requests.post(
                    f"{API_URL}/api/jobs/learn", headers={"X-User-ID": username}
                )
                response.raise_for_status()
                logger.info(f"Aprendizado Concluído ({username})")
            except Exception as e:
                logger.error(f"Falha no aprendizado de {username}: {e}")


# --- Inicialização ---
if not wait_for_api(API_URL):
    logger.warning(
        "Prosseguindo sem confirmação da API (pode falhar nos primeiros jobs)."
    )

# Para testar, vamos rodar a cada 1 minuto as notificações
logger.info("Agendando jobs de notificação a cada 1 minuto.")
schedule.every(1).minutes.do(run_proactive_jobs_for_all_users)

# Faxina diária às 03:00 da manhã
logger.info("Agendando faxina diária para as 03:00.")
schedule.every().day.at("03:00").do(run_sanitize_jobs_for_all_users)

# Aprendizado diário às 04:00 da manhã
logger.info("Agendando aprendizado diário para as 04:00.")
schedule.every().day.at("04:00").do(run_learning_jobs_for_all_users)

# Para teste imediato, vamos agendar uma faxina para daqui a 5 minutos também se quiser,
# mas por agora deixamos o padrão diário.

logger.info("Jobs agendados. Aguardando para executar...")


# --- Loop Principal ---
try:
    while True:
        schedule.run_pending()
        time.sleep(1)  # Dorme por 1 segundo para não fritar a CPU
except KeyboardInterrupt:
    logger.info("Encerrando o agendador...")
