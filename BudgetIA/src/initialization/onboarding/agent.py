# src/initialization/onboarding/agent.py
import logging
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from core.llm_manager import LLMOrchestrator
from initialization.onboarding.state_machine import OnboardingState

logger = logging.getLogger(__name__)


class OnboardingAgent:
    """
    Agente conversacional dedicado ao processo de onboarding.
    Foca em educação, empatia e construção de confiança.
    """

    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.llm_orchestrator = llm_orchestrator
        self.llm = self.llm_orchestrator.get_current_llm()
        self.system_prompt_template = self._load_prompt()
        self.history: list[BaseMessage] = []

    def _load_prompt(self) -> str:
        """Carrega o prompt do arquivo."""
        try:
            import config # Ensure availability
            prompt_path = Path(config.PROMPTS_DIR) / "onboarding_prompt.txt"
            
            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8")

            logger.error(f"Prompt de onboarding não encontrado em {prompt_path}")
            return "Você é um assistente de onboarding útil. Ajude o usuário a configurar sua planilha."

        except Exception as e:
            logger.error(f"Erro ao carregar prompt: {e}")
            return "Você é um assistente de onboarding útil."

    def chat(
        self,
        user_input: str,
        current_state: OnboardingState,
        extra_context: str | None = None,
    ) -> str:
        """
        Processa uma mensagem do usuário dentro do contexto do estado atual.
        """
        # 1. Constrói o contexto do estado
        state_context = f"ESTADO ATUAL: {current_state.name}"
        
        if extra_context:
            state_context += f"\n\nDETALHES DO CONTEXTO:\n{extra_context}"

        # 2. Prepara o System Prompt substituindo o placeholder
        # Se o template não tiver o placeholder, apenas anexa (fallback)
        if "{contexto_estado}" in self.system_prompt_template:
            system_content = self.system_prompt_template.replace(
                "{contexto_estado}", state_context
            )
        else:
            system_content = f"{self.system_prompt_template}\n\nContexto Atual:\n{state_context}"

        messages = [SystemMessage(content=system_content)]

        # 3. Adiciona histórico (limitado para manter foco)
        messages.extend(self.history[-10:])

        # 4. Adiciona mensagem atual
        messages.append(HumanMessage(content=user_input))

        try:
            # 5. Invoca LLM
            response = self.llm.invoke(messages)
            response_text = response.content if hasattr(response, "content") else str(response)

            # 6. Atualiza histórico
            self.history.append(HumanMessage(content=user_input))
            self.history.append(AIMessage(content=response_text))

            return response_text

        except Exception as e:
            logger.error(f"Erro na invocação do LLM de onboarding: {e}")
            if "429" in str(e) or "Rate limit" in str(e):
                return "⚠️ O servidor de IA está sobrecarregado no momento (Rate Limit). Aguarde alguns instantes e tente novamente, ou se preferir, podemos usar a configuração padrão."
            return "Desculpe, tive um pequeno problema técnico. Podemos tentar de novo?"

    def reset_history(self):
        """Limpa o histórico de conversação."""
        self.history = []
