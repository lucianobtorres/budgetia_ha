# src/web_app/💰_BudgetIA.py
import os

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

from typing import Any

import streamlit as st

# --- NOVOS IMPORTS DA CAMADA DE SERVIÇO ---
# Imports do seu projeto
from app.chat_history_manager import StreamlitHistoryManager
from app.chat_service import ChatService
from config import DEFAULT_GEMINI_MODEL
from core.agent_runner_interface import AgentRunner
from core.google_auth_service import GoogleAuthService
from core.llm_enums import LLMProviderType
from core.llm_factory import LLMProviderFactory
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from finance.planilha_manager import PlanilhaManager
from initialization.onboarding_manager import OnboardingManager, OnboardingState
from initialization.system_initializer import initialize_financial_system

# --- Imports dos Novos Módulos de UI ---
from web_app.ui_components import (
    ui_consent,
    ui_fallback,
    ui_file_selection,
    ui_home_hub,
    ui_profile_setup,
    ui_strategy_generation,
)
from web_app.utils import initialize_session_auth

is_logged_in, username, config_service, llm_orchestrator = initialize_session_auth()
if not is_logged_in or not config_service or not llm_orchestrator:
    st.stop()

query_params = st.query_params
if "code" in query_params:
    code = query_params["code"]

    # (Usamos st.empty() para mostrar o status enquanto processamos)
    status_placeholder = st.empty()
    status_placeholder.info("Autenticação com Google recebida. Processando...")

    try:
        auth_service = GoogleAuthService(config_service)
        auth_service.exchange_code_for_tokens(code)

        # Limpa o 'code' da URL
        st.query_params.clear()

        status_placeholder.success(
            "Conta Google conectada com sucesso! Recarregando..."
        )
        st.balloons()

        # --- A CORREÇÃO ---
        # Usamos st.rerun() para forçar a recarga do script com a URL limpa.
        st.rerun()
        # --- FIM DA CORREÇÃO ---

    except Exception as e:
        status_placeholder.error(f"Falha ao processar a autenticação do Google: {e}")

    # Paramos o script aqui de qualquer forma, pois o rerun foi chamado
    st.stop()


# --- Função de Carregamento do Sistema (Cache) ---
@st.cache_resource
def load_financial_system(
    planilha_path: str,
    _llm_orchestrator: LLMOrchestrator,
    _config_service: UserConfigService,
) -> tuple[PlanilhaManager | None, Any | None, Any | None, bool]:
    """
    Carrega o sistema. Usa o _llm_orchestrator como parte da chave de cache.
    """
    print(f"\n--- DEBUG: Entrando em load_financial_system para '{planilha_path}' ---")
    try:
        # --- MODIFICAÇÃO: Passar o LLM Orchestrator para o inicializador ---
        plan_manager, agent_runner, llm_orchestrator_loaded, dados_adicionados = (
            initialize_financial_system(
                planilha_path, _llm_orchestrator, _config_service
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
    primary_provider = LLMProviderFactory.create_provider(
        LLMProviderType.GEMINI, default_model=DEFAULT_GEMINI_MODEL
    )
    orchestrator = LLMOrchestrator(primary_provider=primary_provider)
    orchestrator.get_configured_llm()
    return orchestrator


llm_orchestrator = get_llm_orchestrator()


@st.cache_data(show_spinner=False)
def get_user_config_service(username: str) -> UserConfigService:
    print(f"--- DEBUG APP: Criando UserConfigService para '{username}' ---")
    return UserConfigService(username)


config_service = get_user_config_service(username)

if "onboarding_manager" not in st.session_state:
    st.session_state.onboarding_manager = OnboardingManager(
        llm_orchestrator, config_service
    )

manager: OnboardingManager = st.session_state.onboarding_manager


def load_financial_system_cached(
    _llm_orchestrator: LLMOrchestrator, _config_service: UserConfigService
) -> tuple[PlanilhaManager | None, AgentRunner | None, LLMOrchestrator | None, bool]:
    path = _config_service.get_planilha_path()
    if not path:
        return None, None, None, False

    print(
        f"\n--- DEBUG CACHE: Carregando sistema para usuário '{_config_service.username}' ---"
    )
    return initialize_financial_system(path, _llm_orchestrator, _config_service)


current_state = manager.get_current_state()
print(f"--- DEBUG APP: Estado atual do OnboardingManager: {current_state.name} ---")

validation_callback = lambda path: initialize_financial_system(
    path, llm_orchestrator, config_service
)

# --- ROTEAMENTO DE ESTADO ---

if current_state == OnboardingState.AWAITING_FILE_SELECTION:
    load_financial_system.clear()
    ui_file_selection.render(manager, validation_callback)
    st.stop()

elif current_state == OnboardingState.GENERATING_STRATEGY:
    ui_strategy_generation.render(manager)
    st.stop()

elif current_state == OnboardingState.AWAITING_BACKEND_CONSENT:
    # Instancia o serviço de autenticação
    auth_service = GoogleAuthService(config_service)
    # Renderiza a nova tela
    ui_consent.render(manager, auth_service)
    st.stop()

elif current_state == OnboardingState.STRATEGY_FAILED_FALLBACK:
    ui_fallback.render(manager)
    st.stop()

elif current_state == OnboardingState.SETUP_COMPLETE:
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
    try:
        if "chat_service" not in st.session_state:
            print(
                "--- DEBUG APP: 'chat_service' não está na sessão. Inicializando... ---"
            )
            plan_manager, agent_runner, llm_orchestrator_loaded, dados_adicionados = (
                load_financial_system(
                    current_planilha_path, llm_orchestrator, config_service
                )
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
                    st.cache_data.clear()
                    st.rerun()
                st.stop()

        # Recupera os objetos da sessão
        plan_manager: PlanilhaManager = st.session_state.plan_manager
        # Recupera os NOVOS services
        profile_chat_service: ChatService = st.session_state.profile_chat_service
        main_chat_service: ChatService = st.session_state.main_chat_service

    except Exception as e:
        # Captura a falha de inicialização (como o HttpError 403)
        st.error("🔴 Erro Crítico ao Carregar sua Planilha!", icon="🔥")
        st.warning(f"**Detalhe:** {e}")
        st.info(
            "Isso geralmente acontece se o arquivo está corrompido ou se o BudgetIA não tem mais permissão de *Escrita* nele."
        )

        if st.button("Tentar reconfigurar (Usar outra planilha)"):
            manager.reset_config()
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()

        st.stop()

    is_connected, error_message = plan_manager.check_connection()
    if not is_connected:
        st.error("🔴 **Erro de Conexão com a Planilha!**", icon="📡")
        st.warning(f"**Detalhe:** {error_message}")
        st.info(
            "Isso geralmente acontece se o arquivo foi movido, excluído ou se a permissão de compartilhamento foi revogada."
        )

        if st.button("Tentar reconfigurar (Usar outra planilha)"):
            manager.reset_config()
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()

        st.stop()

    # --- Roteamento FASE 2: Setup do Perfil ---
    if not manager.verificar_perfil_preenchido(plan_manager):
        print("--- DEBUG APP: FASE 2 (Profile Setup) ---")
        ui_profile_setup.render(manager, profile_chat_service, plan_manager)
        st.stop()

    # --- Roteamento FASE 3: Home Hub (Onboarding Completo) ---
    else:
        print("--- DEBUG APP: Onboarding completo. Renderizando Home Hub. ---")
        ui_home_hub.render(plan_manager, main_chat_service)
