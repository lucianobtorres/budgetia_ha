import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Define log level mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_logger(name: str):
    """
    Returns a configured logger instance.
    The log level is determined by the LOG_LEVEL environment variable (default: INFO).
    """
    # 1. Get Log Level from Environment
    env_level = os.getenv("LOG_LEVEL", "INFO").upper()
    level = LOG_LEVELS.get(env_level, logging.INFO)

    # 2. Configure Formatter
    # Format: [Time] [Level] [Module] Message
    # Standard format for text logs
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # 3. Create Handler (Stream to Console/Stdout)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # 4. Configure Logger
    logger = logging.getLogger(name)

    # 5. Avoid adding multiple handlers
    if not logger.handlers:
        logger.addHandler(handler)

        # Persistent Logs (File Handler)
        # On Windows, RotatingFileHandler fails in multi-process (uvicorn reload)
        # We only add it to the main "BudgetIA" logger or if not in a child process
        is_child = (
            os.environ.get("UVICORN_INTERFACES") is not None or "uvicorn" in sys.argv[0]
        )

        # We only add file logging to the main application logger to avoid redundancy
        # and minimize file locks on Windows
        if name == "BudgetIA" or not is_child or os.name != "nt":
            data_dir = os.getenv("DATA_DIR", "./data")
            log_dir = Path(data_dir) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "budgetia.log"

            try:
                # No Windows com Uvicorn Reload, o RotatingFileHandler causa PermissionError no rollover
                # porque múltiplos processos travam o arquivo.
                # Solução: Usar FileHandler simples (sem rotação automática) no Windows Dev.
                if os.name == "nt" and is_child:
                    file_handler = logging.FileHandler(
                        log_file, encoding="utf-8", delay=True
                    )
                else:
                    file_handler = RotatingFileHandler(
                        log_file,
                        maxBytes=10 * 1024 * 1024,
                        backupCount=5,
                        encoding="utf-8",
                        delay=True,
                    )

                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                # Se falhar ao abrir o arquivo (lock), apenas ignoramos o log em arquivo
                # e mantemos o console
                print(f"Aviso: Não foi possível configurar log em arquivo ({e})")

    logger.setLevel(level)

    # Prevent propagation to root logger if using uvicorn/fastapi to avoid double logging
    # logger.propagate = False

    return logger


class EndpointFilter(logging.Filter):
    """
    Filtra logs de acesso que contenham um determinado caminho.
    Útil para suprimir logs de health checks ou arquivos estáticos (/assets, /pwa-...).
    """

    def __init__(self, path: str):
        self.path = path

    def filter(self, record: logging.LogRecord) -> bool:
        # Retorna False se o caminho estiver na mensagem (filtrar fora)
        return record.getMessage().find(self.path) == -1


# Create a default logger for the core application
app_logger = get_logger("BudgetIA")
