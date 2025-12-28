from typing import Any
from core.llm_enums import LLMProviderType
from core.llm_providers.base_provider import LLMProvider
from core.llm_providers.gemini_provider import GeminiProvider
from core.llm_providers.groq_provider import GroqProvider


class LLMProviderFactory:
    """
    Fábrica para criar instâncias de provedores de LLM.
    Permite a extensão para novos provedores sem modificar o código consumidor.
    """

    _REGISTRY: dict[LLMProviderType, type[LLMProvider]] = {
        LLMProviderType.GEMINI: GeminiProvider,
        LLMProviderType.GROQ: GroqProvider,
    }

    @classmethod
    def create_provider(cls, provider_type: LLMProviderType, **kwargs: "Any") -> LLMProvider:
        """
        Cria uma instância do provedor solicitado.
        """
        provider_class = cls._REGISTRY.get(provider_type)

        if not provider_class:
            raise ValueError(
                f"Provedor '{provider_type}' não suportado ou não registrado."
            )

        return provider_class(**kwargs)

    @classmethod
    def get_available_providers(cls) -> list[LLMProviderType]:
        """
        Retorna a lista de tipos de provedores disponíveis.
        """
        return list(cls._REGISTRY.keys())
