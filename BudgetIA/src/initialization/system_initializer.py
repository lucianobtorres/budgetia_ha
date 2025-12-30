# Em: src/initialization/system_initializer.py
import os
import sys

from core.agent_runner_interface import AgentRunner
from core.llm_enums import LLMProviderType
from core.llm_factory import LLMProviderFactory
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService

# Adiciona o 'src' ao path (seu arquivo já deve ter isso)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from infrastructure.agents.factory import AgentFactory
from finance.factory import FinancialSystemFactory
from finance.planilha_manager import PlanilhaManager
from finance.storage.storage_factory import StorageHandlerFactory
from core.logger import get_logger

logger = get_logger("SystemInit")


def initialize_financial_system(
    planilha_path: str,
    llm_orchestrator: LLMOrchestrator,
    config_service: UserConfigService,
) -> tuple[PlanilhaManager | None, AgentRunner | None, LLMOrchestrator | None, bool]:
    """
    Inicializa e conecta todos os componentes do sistema financeiro.
    """

    logger.info(f"Iniciando para '{planilha_path}'")

    plan_manager: PlanilhaManager | None = None
    agent_runner: AgentRunner | None = None
    dados_de_exemplo_foram_adicionados = False

    try:
        # --- 1. Cria o Storage Handler usando a Factory ---
        logger.debug("Criando Storage Handler via Factory...")
        storage_handler = StorageHandlerFactory.create_handler(planilha_path)

        # --- 2. Inicializa o PlanilhaManager usando a FinancialSystemFactory ---
        plan_manager = FinancialSystemFactory.create_manager(
            storage_handler=storage_handler, config_service=config_service
        )
        logger.debug(
            f"PlanilhaManager criado: {type(plan_manager)}"
        )

        is_new_file = plan_manager.is_new_file
        dados_de_exemplo_foram_adicionados = False

        if is_new_file:
            df_transacoes = plan_manager.visualizar_dados(config.NomesAbas.TRANSACOES)
            if not df_transacoes.empty:
                dados_de_exemplo_foram_adicionados = True
                logger.info("Dados de exemplo foram adicionados.")

        # --- 3. Inicialização da IA e do Agente ---
        logger.debug("Configurando LLM e Agente...")
        primary_provider = LLMProviderFactory.create_provider(
            LLMProviderType.GROQ,
            default_model=config.LLMModels.DEFAULT_GROQ,
        )
        # primary_provider = LLMProviderFactory.create_provider(
        #     LLMProviderType.GEMINI, default_model=config.DEFAULT_GEMINI_MODEL
        # )
        llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
        llm_orchestrator.get_configured_llm()

        agent_runner = AgentFactory.create_agent(
            llm_orchestrator=llm_orchestrator,
            plan_manager=plan_manager,
            config_service=config_service,
        )

        logger.info("Inicialização BEM SUCEDIDA.")
        return (
            plan_manager,
            agent_runner,
            llm_orchestrator,
            dados_de_exemplo_foram_adicionados,
        )
    except Exception as e:
        logger.error(f"Erro durante a inicialização: {e}")
        import traceback

        traceback.print_exc()
        return None, None, None, False
