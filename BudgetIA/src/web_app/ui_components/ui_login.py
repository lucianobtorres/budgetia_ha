# src/web_app/ui_components/ui_login.py
from typing import Any

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


# --- 1. FUNÇÃO DE CARREGAMENTO (SEM CACHE) ---
# REMOVIDO: @st.cache_data(show_spinner=False)
def load_auth_config() -> dict[str, Any]:
    """Carrega o arquivo de configuração YAML."""
    try:
        with open("data/users.yaml") as file:
            config = yaml.load(file, Loader=SafeLoader)
            return config
    except FileNotFoundError:
        st.error("Arquivo 'data/users.yaml' não encontrado.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao ler 'data/users.yaml': {e}")
        st.stop()


# --- 2. FUNÇÃO RENDER ATUALIZADA (COM REGISTRO) ---
def render() -> tuple[bool, str | None]:
    """
    Renderiza o componente de login E registro.
    Retorna (True, username) se logado, (False, None) caso contrário.
    """
    config = load_auth_config()

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    # --- 3. RENDERIZAÇÃO DO FORMULÁRIO DE LOGIN E REGISTRO ---
    # Usamos st.tabs para separar o Login do Registro
    tab_login, tab_register = st.tabs(["Login", "Criar Nova Conta"])

    with tab_login:
        authenticator.login()

    with tab_register:
        try:
            if authenticator.register_user(preauthorization=False):
                # Se o registro for bem-sucedido, salvamos o config ATUALIZADO
                # de volta no arquivo YAML
                with open("data/users.yaml", "w") as file:
                    yaml.dump(config, file, default_flow_style=False)
                st.success(
                    'Usuário registrado com sucesso! Por favor, vá para a aba "Login".'
                )
        except Exception as e:
            st.error(e)
    # --- FIM DO FORMULÁRIO ---

    # --- 4. LÓGICA DE VERIFICAÇÃO DE ESTADO (sem mudanças) ---
    if st.session_state["authentication_status"] is False:
        st.error("Usuário ou senha incorretos.")
        return False, None
    elif st.session_state["authentication_status"] is None:
        # Este é o estado "aguardando login", não mostramos aviso
        return False, None
    elif st.session_state["authentication_status"] is True:
        # Usuário logado
        username = st.session_state["username"]

        authenticator.logout("Sair", "sidebar")
        st.sidebar.title(f"Bem-vindo, {st.session_state['name']}!")

        return True, username

    return False, None
