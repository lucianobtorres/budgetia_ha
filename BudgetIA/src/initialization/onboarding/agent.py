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
            # Assume que o arquivo está em src/prompts/onboarding_prompt.txt
            # Ajuste o caminho conforme a estrutura real do projeto
            current_file = Path(__file__)
            project_root = (
                current_file.parent.parent.parent.parent
            )  # src/initialization/onboarding/agent.py -> BudgetIA
            prompt_path = project_root / "src" / "prompts" / "onboarding_prompt.txt"

            if not prompt_path.exists():
                # Fallback para tentar achar relativo ao cwd se estiver rodando da raiz
                prompt_path = Path("src/prompts/onboarding_prompt.txt")

            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8")

            logger.error(f"Prompt de onboarding não encontrado em {prompt_path}")
            return "Você é um assistente de onboarding útil."  # Fallback extremo

        except Exception as e:
            logger.error(f"Erro ao carregar prompt: {e}")
            return "Você é um assistente de onboarding útil."

    def chat(self, user_input: str, current_state: OnboardingState) -> str:
        """
        Processa uma mensagem do usuário dentro do contexto do estado atual.
        """
        # 1. Prepara o System Prompt com o contexto do estado
        system_content = self.system_prompt_template.replace(
            "{contexto_estado}", f"ESTADO ATUAL: {current_state.name}"
        )

        messages = [SystemMessage(content=system_content)]

        # 2. Adiciona histórico (limitado para não estourar contexto se ficar longo)
        # Mantém as últimas 10 mensagens + a atual
        messages.extend(self.history[-10:])

        # 3. Adiciona mensagem atual
        messages.append(HumanMessage(content=user_input))

        try:
            # 4. Invoca LLM
            response = self.llm.invoke(messages)
            response_text = response.content

            # 5. Atualiza histórico
            self.history.append(HumanMessage(content=user_input))
            self.history.append(AIMessage(content=response_text))

            return response_text

        except Exception as e:
            logger.error(f"Erro na invocação do LLM de onboarding: {e}")
            return "Desculpe, tive um pequeno problema técnico. Podemos tentar de novo?"

    def reset_history(self):
        self.history = []
