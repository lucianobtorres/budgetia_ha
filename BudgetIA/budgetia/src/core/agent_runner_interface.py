# src/core/agent_runner_interface.py
from abc import ABC, abstractmethod


class AgentRunner(ABC):
    """
    Interface abstrata para qualquer implementação de agente de IA.
    """

    @abstractmethod
    def interagir(self, user_input: str) -> str:
        """
        Processa a entrada do usuário e retorna a resposta do agente.
        """
        pass

    @abstractmethod
    def interact_with_details(self, user_input: str) -> dict:
        """
        Processa a entrada e retorna resposta + passos intermediários.
        Retorno esperado: {"output": str, "intermediate_steps": list}
        """
        pass

    @property
    @abstractmethod
    def active_llm_info(self) -> str:
        """
        Retorna uma string com informações sobre o LLM ativo.
        """
        pass

    @property
    @abstractmethod
    def chat_history(self) -> list[dict[str, str]]:
        """
        Retorna o histórico de chat atual no formato [{"role": ..., "content": ...}].
        """
        pass

    @chat_history.setter
    @abstractmethod
    def chat_history(self, history: list[dict[str, str]]) -> None:
        """
        Define o histórico de chat.
        """
        pass

    @abstractmethod
    def add_message(self, role: str, content: str) -> None:
        """
        Adiciona uma mensagem isolada à memória do agente.
        role: 'user' ou 'assistant'
        """
        pass
