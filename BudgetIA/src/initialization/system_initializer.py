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
from agent_implementations.factory import AgentFactory
from finance.factory import FinancialSystemFactory
from finance.planilha_manager import PlanilhaManager
from finance.storage.storage_factory import StorageHandlerFactory


def initialize_financial_system(
    planilha_path: str,
    llm_orchestrator: LLMOrchestrator,
    config_service: UserConfigService,
) -> tuple[PlanilhaManager | None, AgentRunner | None, LLMOrchestrator | None, bool]:
    """
    Inicializa e conecta todos os componentes do sistema financeiro.
    """
    print(f"\n--- DEBUG INITIALIZER: Iniciando para '{planilha_path}' ---")

    plan_manager: PlanilhaManager | None = None
    agent_runner: AgentRunner | None = None
    dados_de_exemplo_foram_adicionados = False

    try:
        # --- 1. Cria o Storage Handler usando a Factory ---
        print("--- DEBUG INITIALIZER: Criando Storage Handler via Factory... ---")
        storage_handler = StorageHandlerFactory.create_handler(planilha_path)

        # --- 2. Inicializa o PlanilhaManager usando a FinancialSystemFactory ---
        plan_manager = FinancialSystemFactory.create_manager(
            storage_handler=storage_handler, config_service=config_service
        )
        print(
            f"--- DEBUG INITIALIZER: PlanilhaManager criado: {type(plan_manager)} ---"
        )

        is_new_file = plan_manager.is_new_file
        dados_de_exemplo_foram_adicionados = False

        if is_new_file:
            df_transacoes = plan_manager.visualizar_dados(config.NomesAbas.TRANSACOES)
            if not df_transacoes.empty:
                dados_de_exemplo_foram_adicionados = True
                print("--- DEBUG INITIALIZER: Dados de exemplo foram adicionados. ---")

        # --- 3. Inicialização da IA e do Agente ---
        print("--- DEBUG INITIALIZER: Configurando LLM e Agente... ---")
        primary_provider = LLMProviderFactory.create_provider(
            LLMProviderType.GEMINI, default_model=config.DEFAULT_GEMINI_MODEL
        )
        llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
        llm_orchestrator.get_configured_llm()

        agent_runner = AgentFactory.create_agent(
            llm_orchestrator=llm_orchestrator, plan_manager=plan_manager
        )

        print("--- DEBUG INITIALIZER: Inicialização BEM SUCEDIDA. ---")
        return (
            plan_manager,
            agent_runner,
            llm_orchestrator,
            dados_de_exemplo_foram_adicionados,
        )
    except Exception as e:
        print(f"--- DEBUG INITIALIZER ERROR: Erro durante a inicialização: {e} ---")
        import traceback

        traceback.print_exc()
        return None, None, None, False
