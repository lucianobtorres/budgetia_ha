# src/core/llm_providers/gemini_provider.py

from langchain_google_genai import ChatGoogleGenerativeAI

from .base_provider import LLMProvider


import config

class GeminiProvider(LLMProvider):
    def __init__(
        self,
        default_model: str = config.LLMModels.DEFAULT_GEMINI,
        default_temperature: float = 0.7,
    ):
        super().__init__("GOOGLE_API_KEY", default_model, default_temperature)

    def get_llm(
        self, model_name: str | None = None, temperature: float | None = None
    ) -> ChatGoogleGenerativeAI:
        if not self.api_key:
            raise ValueError("API Key do Gemini não está disponível.")

        model = model_name if model_name else self.default_model
        temp = temperature if temperature is not None else self.default_temperature

        print(f"LOG: Instanciando Gemini LLM: Modelo='{model}', Temp={temp}")

        llm = ChatGoogleGenerativeAI(
            model=model, 
            temperature=temp, 
            google_api_key=self.api_key,
            max_retries=1 # Fail fast on Quota Exceeded
        )

        return llm
