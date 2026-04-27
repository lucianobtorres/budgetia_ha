import os

from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from core.logger import get_logger
from core.memory.memory_service import MemoryService  # NEW
from core.user_config_service import UserConfigService  # NEW
from finance.planilha_manager import PlanilhaManager
from infrastructure.agents.agno_agent import AgnoAgent
from infrastructure.agents.langchain_agent import IADeFinancas

logger = get_logger("AgentFactory")


class AgentFactory:
    """
    Fábrica para criar instâncias de agentes de IA.
    Isola a implementação concreta (LangChain, etc.) do restante do sistema.
    """

    @staticmethod
    def create_agent(
        llm_orchestrator: LLMOrchestrator,
        plan_manager: PlanilhaManager,
        config_service: UserConfigService,  # NEW
    ) -> AgentRunner:
        """
        Cria e retorna uma instância de AgentRunner configurada.
        """
        contexto_perfil = plan_manager.get_perfil_como_texto()

        # Cria o serviço de memória usando o diretório do usuário
        user_dir = config_service.get_user_dir()
        memory_service = MemoryService(user_data_dir=user_dir)

        framework = os.getenv("AGENT_TYPE", "langchain").lower()

        if framework == "agno":
            logger.info("Instanciando Agno Agent")
            return AgnoAgent(
                llm_orchestrator=llm_orchestrator,
                contexto_perfil=contexto_perfil,
                planilha_manager=plan_manager,
            )
        else:
            # Default: LangChain
            return IADeFinancas(
                llm_orchestrator=llm_orchestrator,
                contexto_perfil=contexto_perfil,
                planilha_manager=plan_manager,
                memory_service=memory_service,
                config_service=config_service,
            )
