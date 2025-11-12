# src/web_app/💰_BudgetIA.py
from typing import Any

import streamlit as st

# Imports do seu projeto
import config
from app.chat_history_manager import StreamlitHistoryManager

# --- NOVOS IMPORTS DA CAMADA DE SERVIÇO ---
from app.chat_service import ChatService
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider
from finance.planilha_manager import PlanilhaManager
from initialization.system_initializer import initialize_financial_system
from web_app.onboarding_manager import OnboardingManager

# --- Imports dos Novos Módulos de UI ---
from web_app.ui_components import (
    ui_fallback,
    ui_file_selection,
    ui_home_hub,
    ui_profile_setup,
    ui_strategy_generation,
)

# --- FIM NOVOS IMPORTS ---


# --- Função de Carregamento do Sistema (Cache) ---
@st.cache_resource
def load_financial_system(
    planilha_path: str,
    _llm_orchestrator: LLMOrchestrator,
) -> tuple[PlanilhaManager | None, Any | None, Any | None, bool]:
    """
    Carrega o sistema. Usa o _llm_orchestrator como parte da chave de cache.
    """
    print(f"\n--- DEBUG: Entrando em load_financial_system para '{planilha_path}' ---")
    try:
        # --- MODIFICAÇÃO: Passar o LLM Orchestrator para o inicializador ---
        plan_manager, agent_runner, llm_orchestrator_loaded, dados_adicionados = (
            initialize_financial_system(
                planilha_path, _llm_orchestrator
            )  # Passa o 'llm_orchestrator'
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


# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="BudgetIA",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource
def get_llm_orchestrator() -> LLMOrchestrator:
    """Cria e cacheia o LLMOrchestrator."""
    print("--- DEBUG APP: Criando LLMOrchestrator (cache_resource)... ---")
    primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
    orchestrator = LLMOrchestrator(primary_provider=primary_provider)
    orchestrator.get_configured_llm()
    return orchestrator


llm_orchestrator = get_llm_orchestrator()

if "onboarding_manager" not in st.session_state:
    st.session_state.onboarding_manager = OnboardingManager(llm_orchestrator)

manager: OnboardingManager = st.session_state.onboarding_manager

# --- ROTEADOR PRINCIPAL DA APLICAÇÃO ---

current_state = manager.get_current_state()
print(f"--- DEBUG APP: Estado atual do OnboardingManager: {current_state} ---")

# Define o callback de validação que os módulos de UI precisarão
validation_callback = lambda path: initialize_financial_system(path, llm_orchestrator)


# --- ROTEAMENTO DE ESTADO ---

if current_state == "AWAITING_FILE_SELECTION":
    ui_file_selection.render(manager, validation_callback)

elif current_state == "GENERATING_STRATEGY":
    ui_strategy_generation.render(manager)

elif current_state == "STRATEGY_FAILED_FALLBACK":
    ui_fallback.render(manager)

elif current_state == "SETUP_COMPLETE":
    print("--- DEBUG APP: FASE 1 OK. Carregando sistema... ---")
    current_planilha_path = manager.planilha_path
    if not current_planilha_path:
        st.error(
            "Erro crítico: Estado completo, mas caminho da planilha não encontrado."
        )
        manager.reset_config()
        st.rerun()
        st.stop()

    # --- Carregamento do Sistema ---
    # --- MODIFICAÇÃO: Criar ChatService ---
    if "chat_service" not in st.session_state:
        print("--- DEBUG APP: 'chat_service' não está na sessão. Inicializando... ---")
        plan_manager, agent_runner, llm_orchestrator_loaded, dados_adicionados = (
            load_financial_system(current_planilha_path, llm_orchestrator)
        )
        if plan_manager and agent_runner and llm_orchestrator_loaded:
            # Colocamos os objetos base na sessão para as outras páginas
            st.session_state.plan_manager = plan_manager
            st.session_state.agent_runner = agent_runner
            st.session_state.llm_orchestrator = llm_orchestrator_loaded
            st.session_state.current_planilha_path = current_planilha_path

            # 1. Criar os History Managers Abstraídos
            onboarding_history = StreamlitHistoryManager("onboarding_messages")
            main_chat_history = StreamlitHistoryManager("chat_history")

            # 2. Criar os Chat Services
            # O 'profile_chat_service' usará o histórico de onboarding
            st.session_state.profile_chat_service = ChatService(
                agent_runner=agent_runner, history_manager=onboarding_history
            )
            # O 'main_chat_service' usará o histórico principal
            st.session_state.main_chat_service = ChatService(
                agent_runner=agent_runner, history_manager=main_chat_history
            )
            print("--- DEBUG APP: ChatServices criados e salvos na sessão. ---")

            if (
                dados_adicionados
                and "dados_exemplo_msg_mostrada" not in st.session_state
            ):
                st.success("Dados de exemplo foram carregados na sua planilha!")
                st.session_state.dados_exemplo_msg_mostrada = True
        else:
            st.error("Falha crítica ao carregar componentes do sistema.")
            if st.button("Tentar Novamente (Limpar Configuração)"):
                manager.reset_config()
                st.cache_resource.clear()
                st.rerun()
            st.stop()

    # Recupera os objetos da sessão
    plan_manager: PlanilhaManager = st.session_state.plan_manager
    # Recupera os NOVOS services
    profile_chat_service: ChatService = st.session_state.profile_chat_service
    main_chat_service: ChatService = st.session_state.main_chat_service
    # --- FIM DA MODIFICAÇÃO ---

    # --- Roteamento FASE 2: Setup do Perfil ---
    if not manager.verificar_perfil_preenchido(plan_manager):
        print("--- DEBUG APP: FASE 2 (Profile Setup) ---")
        # --- MODIFICAÇÃO: Passa o profile_chat_service para a UI ---
        ui_profile_setup.render(manager, profile_chat_service, plan_manager)

    # --- Roteamento FASE 3: Home Hub (Onboarding Completo) ---
    else:
        print("--- DEBUG APP: Onboarding completo. Renderizando Home Hub. ---")
        # --- MODIFICAÇÃO: Passa o main_chat_service para a UI ---
        ui_home_hub.render(plan_manager, main_chat_service)
