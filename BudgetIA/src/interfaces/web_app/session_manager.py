
import os
import yaml
import streamlit as st
import streamlit_authenticator as stauth
from typing import Any
from yaml.loader import SafeLoader
from pathlib import Path

from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from core.llm_providers.groq_provider import GroqProvider
from config import DEFAULT_GROQ_MODEL
from interfaces.web_app.ui_components.ui_login import LoginUI

# TODO: Cache resource might need to be moved to a simpler provider if pickling issues arise
@st.cache_resource
def get_llm_orchestrator() -> LLMOrchestrator:
    """Cria e cacheia o LLMOrchestrator."""
    print("--- DEBUG SESSION: Criando LLMOrchestrator (cache_resource)... ---")
    primary_provider = GroqProvider(default_model=DEFAULT_GROQ_MODEL)
    orchestrator = LLMOrchestrator(primary_provider=primary_provider)
    orchestrator.get_configured_llm()
    return orchestrator

class SessionManager:
    """Gerencia a sessão do usuário, autenticação e inicialização de serviços fundamentais."""

    @staticmethod
    def load_auth_config() -> dict[str, Any]:
        """Carrega configurarão de auth do YAML."""
        try:
            with open("data/users.yaml") as file:
                data = yaml.load(file, Loader=SafeLoader)
                if isinstance(data, dict):
                    return data
                return {}
        except FileNotFoundError:
            st.error("Arquivo 'data/users.yaml' não encontrado.")
            st.stop()
        except Exception as e:
            st.error(f"Erro ao ler 'data/users.yaml': {e}")
            st.stop()

    @staticmethod
    def initialize_session() -> tuple[bool, str | None, UserConfigService | None, LLMOrchestrator | None]:
        """
        Ponto de entrada único para autenticação e setup da sessão.
        Retorna (is_logged_in, username, config_service, llm_orchestrator).
        """
        auth_config = SessionManager.load_auth_config()
        llm_orchestrator = get_llm_orchestrator()

        # Configura o validador para aceitar qualquer coisa por padrão (bypass complex validation issues)
        if "validator" not in auth_config:
            auth_config["validator"] = "^.*$"

        authenticator = stauth.Authenticate(
            auth_config["credentials"],
            auth_config["cookie"]["name"],
            auth_config["cookie"]["key"],
            auth_config["cookie"]["expiry_days"],
            validator="^.*$",
        )
        authenticator.validator = "^.*$" # Force override

        # --- Lógica de UI vs Estado ---
        if st.session_state.get("authentication_status") is not True:
            LoginUI.render(authenticator, auth_config)
            return False, None, None, None
        
        # --- Usuário Logado ---
        username = st.session_state["username"]
        authenticator.logout("Sair", "sidebar")
        st.sidebar.title(f"Bem-vindo, {st.session_state.get('name', username)}!")

        # Inicializa UserConfigService
        config_service = UserConfigService(username)

        # Inicializa API Client se necessário
        SessionManager._ensure_api_client(username)

        # Executa rotinas de background (toasts, notificações)
        SessionManager._run_background_routines()

        return True, username, config_service, llm_orchestrator

    @staticmethod
    def _ensure_api_client(username: str) -> None:
        """Garante que o Cliente da API esteja instanciado na sessão."""
        if "api_client" not in st.session_state:
            from interfaces.web_app.api_client import BudgetAPIClient
            api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
            st.session_state.api_client = BudgetAPIClient(base_url=api_url, user_id=username)

    @staticmethod
    def _run_background_routines() -> None:
        """Executa verificações leves de background (Heartbeat, Toasts)."""
        try:
            client = st.session_state.api_client
            client.send_heartbeat()
            
            # Toasts
            toasts = client.get_toasts()
            if toasts:
                for t in toasts:
                    st.toast(t.get("message"), icon=t.get("icon", "🔔"))
            
            # Notificações na Sidebar
            unread = client.get_unread_count()
            if unread > 0:
                st.sidebar.markdown(f"### 🔔 **{unread} Notificações**")
                st.sidebar.info("Vá para a página **Notificações** para ver os detalhes.")
        except Exception:
            pass

# Alias para compatibilidade com código existente
initialize_session_auth = SessionManager.initialize_session
