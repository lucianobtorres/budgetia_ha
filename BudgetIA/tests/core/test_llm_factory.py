import pytest
from core.llm_factory import LLMProviderFactory
from core.llm_enums import LLMProviderType
from core.llm_providers.gemini_provider import GeminiProvider

def test_factory_creates_gemini_provider():
    provider = LLMProviderFactory.create_provider(LLMProviderType.GEMINI)
    assert isinstance(provider, GeminiProvider)
    assert provider.name == "Gemini"  # Nome retornado pela propriedade name

def test_factory_raises_error_for_invalid_provider():
    with pytest.raises(ValueError):
        # Forçando um tipo inválido para testar a validação
        LLMProviderFactory.create_provider("invalid_provider") # type: ignore

def test_get_available_providers():
    providers = LLMProviderFactory.get_available_providers()
    assert LLMProviderType.GEMINI in providers
