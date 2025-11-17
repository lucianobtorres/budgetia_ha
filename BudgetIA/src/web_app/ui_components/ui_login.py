# src/web_app/ui_components/ui_login.py
from typing import Any

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


# A função de carregar o config (sem cache) está correta
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

    # --- 1. CORREÇÃO DE UX: VERIFICAR O ESTADO ANTES DE RENDERIZAR ---
    # Se o usuário JÁ ESTÁ logado, apenas renderize o 'logout' e retorne True.
    if st.session_state["authentication_status"] is True:
        username = st.session_state["username"]
        authenticator.logout("Sair", "sidebar")
        st.sidebar.title(f"Bem-vindo, {st.session_state['name']}!")
        return True, username
    # --- FIM DA CORREÇÃO DE UX ---

    # --- 2. RENDERIZAÇÃO (Se não estiver logado) ---
    # Se não estava logado, mostre as abas de Login/Registro
    tab_login, tab_register = st.tabs(["Login", "Criar Nova Conta"])

    with tab_login:
        authenticator.login()

    with tab_register:
        try:
            # --- 3. CORREÇÃO DO ERRO 'preauthorization' ---
            # Removemos o argumento que causou o TypeError
            if authenticator.register_user():
                # --- FIM DA CORREÇÃO DO ERRO ---
                # Se o registro for bem-sucedido, salvamos o config ATUALIZADO
                with open("data/users.yaml", "w") as file:
                    yaml.dump(config, file, default_flow_style=False)
                st.success(
                    'Usuário registrado com sucesso! Por favor, vá para a aba "Login".'
                )
        except Exception as e:
            st.error(e)

    # --- 4. VERIFICAÇÃO DE ESTADO PÓS-INTERAÇÃO ---
    if st.session_state["authentication_status"] is False:
        st.error("Usuário ou senha incorretos.")
        return False, None

    # Se o status for None (aguardando login), não é um erro.
    return False, None
