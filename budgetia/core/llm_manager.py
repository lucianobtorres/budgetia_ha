# src/core/llm_manager.py
from typing import Any

from dotenv import load_dotenv

# Importa a interface e as implementações concretas
from .llm_providers.base_provider import LLMProvider

load_dotenv()


class LLMOrchestrator:
    """
    Orquestra a seleção de LLMs, permitindo a configuração de modelos primários e de fallback.
    """

    def __init__(
        self,
        primary_provider: LLMProvider,
        fallback_providers: list[LLMProvider] | None = None,
    ):
        self.primary_provider = primary_provider
        self.fallback_providers = (
            fallback_providers if fallback_providers is not None else []
        )
        self._active_llm: Any | None = None
        self._active_provider_name: str | None = None
        self._active_model_name: str | None = None

    @property
    def active_llm(self) -> Any | None:
        """Retorna a instância do LLM atualmente ativa."""
        return self._active_llm

    @property
    def active_provider_name(self) -> str | None:
        """Retorna o nome do provedor do LLM atualmente ativo."""
        return self._active_provider_name

    @property
    def active_model_name(self) -> str | None:
        """Retorna o nome do modelo do LLM atualmente ativo."""
        return self._active_model_name

    def get_configured_llm(
        self, model_name: str | None = None, temperature: float | None = None
    ) -> Any:
        """
        Tenta obter o LLM do provedor primário e, em caso de falha, tenta os provedores de fallback.
        """
        providers_to_try = [self.primary_provider] + self.fallback_providers

        for provider in providers_to_try:
            try:
                if not provider.api_key:
                    print(
                        f"AVISO: Pulando provedor '{provider.name}' pois a API Key não foi encontrada."
                    )
                    continue

                llm = provider.get_llm(model_name, temperature)
                self._active_llm = llm
                self._active_provider_name = provider.name

                if hasattr(llm, "model_name") and llm.model_name:
                    self._active_model_name = str(llm.model_name)
                elif hasattr(llm, "model") and llm.model:
                    self._active_model_name = str(llm.model)
                else:
                    self._active_model_name = provider.default_model

                print(
                    f"LOG: LLM ativo: Provedor='{self._active_provider_name}', Modelo='{self._active_model_name}'."
                )
                return llm
            except Exception as e:
                print(f"ERRO: Falha ao carregar LLM do provedor '{provider.name}': {e}")

        raise RuntimeError("Nenhum provedor de LLM pôde ser carregado.")

    def get_current_llm(self) -> Any:
        """Retorna o LLM ativo, configurando-o se necessário."""
        if self._active_llm is None:
            self.get_configured_llm()
        return self._active_llm

    @property
    def active_llm_info(self) -> str:
        """Retorna uma string formatada com as informações do LLM ativo."""
        if self._active_provider_name and self._active_model_name:
            return (
                f"Usando IA: {self._active_provider_name} - {self._active_model_name}"
            )
        return "IA não carregada."
