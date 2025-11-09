# src/initialization/system_initializer.py
import os
import sys

import config

# Adiciona o diretório 'src' ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    # Importa APENAS o load_persistent_config
    from web_app.utils import load_persistent_config
except ImportError as e:
    print(f"ERRO CRÍTICO: Não foi possível importar 'web_app.utils': {e}.")

    def load_persistent_config() -> dict:
        return {}

    # PLANILHA_KEY não é necessário aqui, quebrando o ciclo.

from agent_implementations.langchain_agent import IADeFinancas
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider
from finance.excel_handler import ExcelHandler

# Importa a Fachada
from finance.planilha_manager import PlanilhaManager

# Importa a função de utils (para quebrar o ciclo)


def initialize_financial_system(
    planilha_path: str,
) -> tuple[PlanilhaManager | None, AgentRunner | None, LLMOrchestrator | None, bool]:
    """
    Inicializa e conecta todos os componentes do sistema financeiro.
    Retorna a fachada PlanilhaManager (para a UI) e o AgentRunner (com DIP).
    """
    print(f"\n--- DEBUG INITIALIZER: Iniciando para '{planilha_path}' ---")
    plan_manager: PlanilhaManager | None = None
    agent_runner: AgentRunner | None = None
    llm_orchestrator: LLMOrchestrator | None = None
    dados_de_exemplo_foram_adicionados = False

    try:
        config_persistente = load_persistent_config()
        mapeamento = config_persistente.get("mapeamento")

        if mapeamento:
            print("--- DEBUG INITIALIZER: Mapeamento de usuário encontrado! ---")
        else:
            print(
                "--- DEBUG INITIALIZER: Nenhum mapeamento encontrado, usando layout padrão. ---"
            )

        excel_handler = ExcelHandler(file_path=planilha_path)

        # --- 1. Inicialização do Gerenciador (Fachada) ---
        print("--- DEBUG INITIALIZER: Criando PlanilhaManager (Fachada)... ---")
        plan_manager = PlanilhaManager(
            excel_handler=excel_handler,
            mapeamento=mapeamento,
        )
        print(
            f"--- DEBUG INITIALIZER: PlanilhaManager criado: {type(plan_manager)} ---"
        )

        is_new_file = plan_manager.is_new_file

        # A lógica de popular dados já está no __init__ do PlanilhaManager
        if is_new_file and mapeamento is None:
            # Apenas verificamos se os dados foram realmente adicionados
            # Esta linha agora funciona, pois o plan_manager tem o transaction_repo
            if not plan_manager.transaction_repo.get_all_transactions().empty:
                dados_de_exemplo_foram_adicionados = True
                print("--- DEBUG INITIALIZER: Dados de exemplo foram adicionados. ---")

        # --- 2. Inicialização da IA e do Agente ---
        print("--- DEBUG INITIALIZER: Configurando LLM e Agente... ---")
        primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
        llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
        llm_orchestrator.get_configured_llm()

        contexto_perfil = plan_manager.get_perfil_como_texto()
        print(
            f"--- DEBUG INITIALIZER: Contexto do Perfil injetado no Agente: {contexto_perfil[:50]}... ---"
        )

        # --- PONTO-CHAVE (DIP) ---
        # O Agente (IADeFinancas) recebe os repositórios, NÃO a fachada.
        agent_runner = IADeFinancas(
            llm_orchestrator=llm_orchestrator,
            contexto_perfil=contexto_perfil,
            data_context=plan_manager._context,
            transaction_repo=plan_manager.transaction_repo,
            budget_repo=plan_manager.budget_repo,
            debt_repo=plan_manager.debt_repo,
            profile_repo=plan_manager.profile_repo,
            insight_repo=plan_manager.insight_repo,
        )
        # --- FIM DO PONTO-CHAVE ---

        print("--- DEBUG INITIALIZER: Inicialização BEM SUCEDIDA. ---")

        return (
            plan_manager,  # Retorna a fachada para a UI (Streamlit)
            agent_runner,  # Retorna o agente para a UI (Streamlit)
            llm_orchestrator,
            dados_de_exemplo_foram_adicionados,
        )

    except Exception as e:
        print(f"--- DEBUG INITIALIZER ERROR: Erro durante a inicialização: {e} ---")
        import traceback

        traceback.print_exc()
        return None, None, None, False
