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
    
    # Avoid adding multiple handlers if get_logger is called repeatedly for the same name
    if not logger.handlers:
        logger.addHandler(handler)

        # 5. File Handler (Persistent Logs)
        # Determine Data Dir safely (avoid circular import with config.py)
        data_dir = os.getenv("DATA_DIR", "./data")
        log_dir = Path(data_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "budgetia.log"
        
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
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
