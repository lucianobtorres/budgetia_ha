# src/core/llm_providers/groq_provider.py

from langchain_groq import ChatGroq
from pydantic.types import SecretStr

from .base_provider import LLMProvider
from core.logger import get_logger

logger = get_logger("GroqProvider")


class GroqProvider(LLMProvider):
    def __init__(
        self, default_model: str = "llama3-8b-8192", default_temperature: float = 0.7
    ):
        super().__init__("GROQ_API_KEY", default_model, default_temperature)

    def get_llm(
        self, model_name: str | None = None, temperature: float | None = None
    ) -> ChatGroq:
        if not self.api_key:
            raise ValueError("API Key do Groq não está disponível.")

        model = model_name if model_name else self.default_model
        temp = temperature if temperature is not None else self.default_temperature

        logger.info(f"Instanciando Groq LLM: Modelo='{model}', Temp={temp}")

        return ChatGroq(model=model, temperature=temp, api_key=SecretStr(self.api_key))
