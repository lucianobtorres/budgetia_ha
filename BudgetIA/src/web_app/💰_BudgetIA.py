# src/web_app/💰_BudgetIA.py
import os
import streamlit as st
from typing import Any

# --- Environment Setup ---
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

# --- Imports ---
from app.chat_history_manager import StreamlitHistoryManager
from app.chat_service import ChatService
from config import DEFAULT_GEMINI_MODEL
from core.agent_runner_interface import AgentRunner
from core.llm_enums import LLMProviderType
from core.llm_factory import LLMProviderFactory
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from finance.planilha_manager import PlanilhaManager
from initialization.onboarding.orchestrator import OnboardingOrchestrator, OnboardingState
from initialization.system_initializer import initialize_financial_system
from web_app.ui_components import ui_home_hub, ui_onboarding_chat
from web_app.utils import initialize_session_auth

# --- Functions ---

def setup_page():
    st.set_page_config(
        page_title="BudgetIA",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

@st.cache_resource
def load_financial_system(
    planilha_path: str,
    _llm_orchestrator: LLMOrchestrator,
    _config_service: UserConfigService,
) -> tuple[PlanilhaManager | None, Any | None, Any | None, bool]:
    """Carrega o sistema financeiro (PlanilhaManager, AgentRunner, etc.)."""
    print(f"\n--- DEBUG: Entrando em load_financial_system para '{planilha_path}' ---")
    try:
        plan_manager, agent_runner, llm_orchestrator_loaded, dados_adicionados = (
            initialize_financial_system(
                planilha_path, _llm_orchestrator, _config_service
            )
        )
        if plan_manager and agent_runner and llm_orchestrator_loaded:
            print("--- DEBUG: load_financial_system retornando objetos válidos. ---")
            return (
                plan_manager,
                agent_runner,
                llm_orchestrator_loaded,
                dados_adicionados,
            )
        else:
            st.error("Falha interna ao inicializar componentes.")
            st.stop()
            return None, None, None, False
    except Exception as e:
        print(f"--- DEBUG ERROR: Exception em load_financial_system: {e} ---")
        st.error(f"Erro inesperado ao carregar sistema: {e}")
        st.stop()
        return None, None, None, False

def run_onboarding(username: str, config_service: UserConfigService, llm_orchestrator: LLMOrchestrator):
    """Executa o fluxo de onboarding."""
    if "onboarding_orchestrator" not in st.session_state:
        print(f"--- DEBUG APP: Criando OnboardingOrchestrator para '{username}' ---")
        st.session_state.onboarding_orchestrator = OnboardingOrchestrator(
            config_service, llm_orchestrator
        )
    
    orchestrator: OnboardingOrchestrator = st.session_state.onboarding_orchestrator
    ui_onboarding_chat.render(orchestrator)

def run_main_app(username: str, config_service: UserConfigService, llm_orchestrator: LLMOrchestrator, planilha_path: str):
    """Executa a aplicação principal (Home Hub)."""
    print("--- DEBUG APP: Onboarding completo. Carregando sistema... ---")
    
    try:
        if "chat_service" not in st.session_state:
            plan_manager, agent_runner, llm_orchestrator_loaded, dados_adicionados = (
                load_financial_system(planilha_path, llm_orchestrator, config_service)
            )
            
            if plan_manager and agent_runner and llm_orchestrator_loaded:
                st.session_state.plan_manager = plan_manager
                st.session_state.agent_runner = agent_runner
                st.session_state.llm_orchestrator = llm_orchestrator_loaded
                st.session_state.current_planilha_path = planilha_path

                # History Managers
                onboarding_history = StreamlitHistoryManager("onboarding_messages")
                main_chat_history = StreamlitHistoryManager("chat_history")

                # Chat Services
                st.session_state.profile_chat_service = ChatService(
                    agent_runner=agent_runner, history_manager=onboarding_history
                )
                st.session_state.main_chat_service = ChatService(
                    agent_runner=agent_runner, history_manager=main_chat_history
                )
                
                if dados_adicionados and "dados_exemplo_msg_mostrada" not in st.session_state:
                    st.success("Dados de exemplo foram carregados na sua planilha!")
                    st.session_state.dados_exemplo_msg_mostrada = True
            else:
                st.error("Falha crítica ao carregar componentes do sistema.")
                if st.button("Tentar Novamente (Limpar Configuração)"):
                    config_service.clear_config()
                    st.cache_resource.clear()
                    st.cache_data.clear()
                    st.rerun()
                st.stop()

        # Recupera objetos da sessão
        plan_manager = st.session_state.plan_manager
        main_chat_service = st.session_state.main_chat_service

        # Verifica conexão
        is_connected, error_message = plan_manager.check_connection()
        if not is_connected:
            st.error("🔴 **Erro de Conexão com a Planilha!**", icon="📡")
            st.warning(f"**Detalhe:** {error_message}")
            if st.button("Tentar reconfigurar (Usar outra planilha)"):
                config_service.clear_config()
                st.cache_resource.clear()
                st.cache_data.clear()
                st.rerun()
            st.stop()

        # Renderiza Home Hub
        ui_home_hub.render(plan_manager, main_chat_service)

    except Exception as e:
        st.error("🔴 Erro Crítico ao Carregar sua Planilha!", icon="🔥")
        st.warning(f"**Detalhe:** {e}")
        if st.button("Tentar reconfigurar (Usar outra planilha)"):
            config_service.clear_config()
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()
        st.stop()

def main():
    setup_page()
    
    # Autenticação e Inicialização de Sessão
    is_logged_in, username, config_service, llm_orchestrator = initialize_session_auth()
    if not is_logged_in or not config_service or not llm_orchestrator:
        st.stop()

    # Verifica Status do Onboarding
    saved_status = config_service.get_onboarding_status()
    
    if saved_status == OnboardingState.COMPLETE.name:
        current_planilha_path = config_service.get_planilha_path()
        if not current_planilha_path:
            st.error("Erro crítico: Estado completo, mas caminho da planilha não encontrado.")
            if st.button("Resetar Configuração"):
                config_service.clear_config()
                st.rerun()
            st.stop()
            
        run_main_app(username, config_service, llm_orchestrator, current_planilha_path)
    else:
        run_onboarding(username, config_service, llm_orchestrator)

if __name__ == "__main__":
    main()
