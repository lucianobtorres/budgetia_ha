# src/app/chat_service.py


import config
from app.chat_history_manager import BaseHistoryManager
from core.agent_runner_interface import AgentRunner
from core.cache_service import CacheService

CHAT_LIMIT_PER_HOUR = 100
CHAT_LIMIT_EXPIRE = 3600


class ChatService:
    """
    Orquestra a interação entre o usuário, o histórico de chat
    e o agente de IA.

    Esta classe é agnóstica de UI (não sabe sobre Streamlit).
    """

    def __init__(self, agent_runner: AgentRunner, history_manager: BaseHistoryManager):
        self.agent_runner = agent_runner
        self.history_manager = history_manager
        self.cache_service = CacheService(config.UPSTASH_REDIS_URL)

    def add_first_message(self, content: str) -> None:
        """Adiciona a primeira mensagem do assistente se o histórico estiver vazio."""
        if not self.get_history():
            # Adiciona ao histórico da UI
            self.history_manager.add_message("assistant", content)

            # Adiciona também à memória do agente (via interface abstrata)
            self.agent_runner.add_message("assistant", content)

    def get_history(self) -> list[dict[str, str]]:
        """Retorna o histórico de chat da UI."""
        return self.history_manager.get_history()

    def handle_message(self, user_prompt: str, user_id: str) -> str:
        """
        Processa uma mensagem do usuário, salva no histórico
        e retorna a resposta da IA.
        """
        rate_limit_key = f"rate:chat:{user_id}"
        if self.cache_service.check_rate_limit(
            rate_limit_key, CHAT_LIMIT_PER_HOUR, CHAT_LIMIT_EXPIRE
        ):
            return (
                "Desculpe, você atingiu o limite de mensagens por hora. "
                "Por favor, tente novamente mais tarde."
            )

        try:
            # 1. Salva a mensagem do usuário no histórico da UI
            self.history_manager.add_message("user", user_prompt)

            # 2. Chama o agente (que usa sua própria memória interna para contexto)
            response = self.agent_runner.interagir(user_prompt)

            # 3. Salva a resposta da IA no histórico da UI
            self.history_manager.add_message("assistant", response)

            return str(response)
        except Exception as e:
            return f"Ocorreu um erro ao processar sua mensagem: {e}"

    def handle_profile_message(
        self, user_prompt: str, profile_prompt_template: str
    ) -> str:
        """
        Processa uma mensagem do usuário durante o onboarding de perfil.
        """
        # 1. Salva a mensagem do usuário no histórico da UI
        self.history_manager.add_message("user", user_prompt)

        # 2. Prepara o prompt guiado
        prompt_guiado = profile_prompt_template.format(prompt=user_prompt)

        # 3. Chama o agente com o prompt guiado
        response = self.agent_runner.interagir(prompt_guiado)

        # 4. Salva a resposta da IA no histórico da UI
        self.history_manager.add_message("assistant", response)

        return response
