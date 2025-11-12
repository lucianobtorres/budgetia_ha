# src/app/chat_service.py


from app.chat_history_manager import BaseHistoryManager
from core.agent_runner_interface import AgentRunner


class ChatService:
    """
    Orquestra a interação entre o usuário, o histórico de chat
    e o agente de IA.

    Esta classe é agnóstica de UI (não sabe sobre Streamlit).
    """

    def __init__(self, agent_runner: AgentRunner, history_manager: BaseHistoryManager):
        self.agent_runner = agent_runner
        self.history_manager = history_manager

    def add_first_message(self, content: str) -> None:
        """Adiciona a primeira mensagem do assistente se o histórico estiver vazio."""
        if not self.get_history():
            # Adiciona ao histórico da UI
            self.history_manager.add_message("assistant", content)

            # Adiciona também à memória do agente
            if hasattr(self.agent_runner, "memory"):
                self.agent_runner.memory.chat_memory.add_ai_message(content)

    def get_history(self) -> list[dict[str, str]]:
        """Retorna o histórico de chat da UI."""
        return self.history_manager.get_history()

    def handle_message(self, user_prompt: str) -> str:
        """
        Processa uma mensagem do usuário, salva no histórico
        e retorna a resposta da IA.
        """
        # 1. Salva a mensagem do usuário no histórico da UI
        self.history_manager.add_message("user", user_prompt)

        # 2. Chama o agente (que usa sua própria memória interna para contexto)
        response = self.agent_runner.interagir(user_prompt)

        # 3. Salva a resposta da IA no histórico da UI
        self.history_manager.add_message("assistant", response)

        return response

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
