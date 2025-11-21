from agent_implementations.langchain_agent import IADeFinancas
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from finance.planilha_manager import PlanilhaManager


class AgentFactory:
    """
    Fábrica para criar instâncias de agentes de IA.
    Isola a implementação concreta (LangChain, etc.) do restante do sistema.
    """

    @staticmethod
    def create_agent(
        llm_orchestrator: LLMOrchestrator, plan_manager: PlanilhaManager
    ) -> AgentRunner:
        """
        Cria e retorna uma instância de AgentRunner configurada.
        """
        contexto_perfil = plan_manager.get_perfil_como_texto()

        return IADeFinancas(
            llm_orchestrator=llm_orchestrator,
            contexto_perfil=contexto_perfil,
            data_context=plan_manager._context,
            transaction_repo=plan_manager.transaction_repo,
            budget_repo=plan_manager.budget_repo,
            debt_repo=plan_manager.debt_repo,
            profile_repo=plan_manager.profile_repo,
            insight_repo=plan_manager.insight_repo,
        )
