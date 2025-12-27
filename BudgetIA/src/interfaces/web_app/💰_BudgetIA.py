# src/web_app/💰_BudgetIA.py
import os
import streamlit as st
from typing import Any

# --- Environment Setup ---
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

# --- Imports ---
# --- Imports ---
from application.chat_history_manager import StreamlitHistoryManager
from config import DEFAULT_GEMINI_MODEL, UPSTASH_REDIS_URL
from core.llm_enums import LLMProviderType
from core.llm_factory import LLMProviderFactory
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from initialization.onboarding.orchestrator import OnboardingOrchestrator, OnboardingState
from interfaces.web_app.ui_components import ui_home_hub, ui_onboarding_chat
from interfaces.web_app.session_manager import SessionManager # NEW
from interfaces.web_app.api_client import BudgetAPIClient

# --- Cache Setup (LangChain) ---
try:
    if UPSTASH_REDIS_URL:
        import redis
        from langchain.globals import set_llm_cache
        from langchain_community.cache import RedisCache

        # Força protocolo seguro se necessário e remove args incompatíveis
        real_url = UPSTASH_REDIS_URL
        if real_url.startswith("redis://") and not real_url.startswith("rediss://"):
             # Upstash geralmente precisa de rediss://
             real_url = real_url.replace("redis://", "rediss://")

        # Configura Cache Global do LangChain
        # decode_responses=False pois o cache usa pickle
        redis_client = redis.from_url(real_url, decode_responses=False)
        set_llm_cache(RedisCache(redis_client))
        print("LOG: LangChain Redis Cache (Global) ENABLED. 🚀")
except Exception as e:
    print(f"AVISO: Falha ao ativar Cache de LLM: {e}")

# --- Functions ---

def setup_page():
    st.set_page_config(
        page_title="BudgetIA",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

# load_financial_system removido (substituído pela API)

def run_onboarding(username: str, config_service: UserConfigService, llm_orchestrator: LLMOrchestrator):
    """Executa o fluxo de onboarding (Via API)."""
    # Garante que o cliente da API esteja disponível
    if "api_client" not in st.session_state:
        SessionManager._ensure_api_client(username)
    
    api_client: BudgetAPIClient = st.session_state.api_client
    ui_onboarding_chat.render(api_client)

def run_main_app(username: str, config_service: UserConfigService, llm_orchestrator: LLMOrchestrator, planilha_path: str):
    """Executa a aplicação principal (Home Hub) via API."""
    
    # Inicializa Cliente da API
    if "api_client" not in st.session_state:
        # Passa o username logado para o cliente
        client = BudgetAPIClient(user_id=username)
        if not client.is_healthy():
            st.error("🔴 **API Offline!**", icon="🔌")
            st.info("Por favor, execute `poetry run start-api` no terminal para iniciar o backend.")
            if st.button("Verificar Novamente"):
                st.rerun()
            st.stop()
        else:
            st.session_state.api_client = client
            st.success(f"Conectado à API como {username}!", icon="🟢")

    api_client: BudgetAPIClient = st.session_state.api_client
    st.session_state.current_planilha_path = planilha_path

    # Renderiza Home Hub usando o Cliente API
    ui_home_hub.render(api_client)

def main():
    setup_page()
    
    # Autenticação e Inicialização de Sessão
    # Agora usando o SessionManager (Padrão SRP)
    is_logged_in, username, config_service, llm_orchestrator = SessionManager.initialize_session()
    
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
