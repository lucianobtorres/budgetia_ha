# src/core/llm_providers/openai_provider.py
from langchain_openai import ChatOpenAI
from pydantic.types import SecretStr

import config
from .base_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        default_model: str = config.LLMModels.OPENAI_GPT_3_5_TURBO,
        default_temperature: float = 0.7,
    ):
        super().__init__("OPENAI_API_KEY", default_model, default_temperature)

    def get_llm(
        self, model_name: str | None = None, temperature: float | None = None
    ) -> ChatOpenAI:
        if not self.api_key:
            raise ValueError("API Key da OpenAI não está disponível.")

        model = model_name if model_name else self.default_model
        temp = temperature if temperature is not None else self.default_temperature

        print(f"LOG: Instanciando OpenAI LLM: Modelo='{model}', Temp={temp}")

        return ChatOpenAI(
            model=model, temperature=temp, api_key=SecretStr(self.api_key)
        )
