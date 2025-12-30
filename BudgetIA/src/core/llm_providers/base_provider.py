# src/core/llm_providers/base_provider.py
import os
from abc import ABC, abstractmethod
from typing import Any

from core.logger import get_logger

logger = get_logger("LLM_Provider")

class LLMProvider(ABC):
    """
    Interface abstrata para qualquer provedor de Large Language Model.
    Define o contrato que todo provedor de LLM deve seguir.
    """

    def __init__(
        self, api_key_env_var: str, default_model: str, default_temperature: float = 0.7
    ):
        self.api_key = os.getenv(api_key_env_var)
        if not self.api_key:
            logger.warning(
                f"Chave da API para '{api_key_env_var}' não encontrada. Este provedor pode não funcionar."
            )
        else:
            logger.info(
                f"Chave da API para {self.__class__.__name__} carregada com sucesso!"
            )

        self.api_key_env_var = api_key_env_var
        self.default_model = default_model
        self.default_temperature = default_temperature

    @abstractmethod
    def get_llm(
        self, model_name: str | None = None, temperature: float | None = None
    ) -> Any:
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__.replace("Provider", "")
