
import yaml
import streamlit as st
import streamlit_authenticator as stauth

from typing import Any

class LoginUI:
    @staticmethod
    def render(authenticator: stauth.Authenticate, auth_config: dict[str, Any]) -> None:
        """Renderiza a interface de login e registro."""
        
        # Define Abas para Login e Registro
        tab_login, tab_register = st.tabs(["🔐 Entrar", "📝 Criar Nova Conta"])

        with tab_login:
            authenticator.login()
            if st.session_state["authentication_status"] is False:
                st.error("Usuário ou senha incorretos.")
            elif st.session_state["authentication_status"] is None:
                st.warning("Por favor, faça o login para acessar o BudgetIA.")

        with tab_register:
            LoginUI._render_register_tab(auth_config)

    @staticmethod
    def _render_register_tab(auth_config: dict[str, Any]) -> None:
        """Renderiza a aba de registro."""
        st.info(
            "ℹ️ **Requisitos:**\n"
            "- **Todos** os campos são obrigatórios.\n"
            "- **Senha:** Mínimo 6 caracteres (simples)."
        )

        try:
            with st.form("register_form"):
                st.write("Preencha seus dados:")
                new_name = st.text_input("Nome")
                new_email = st.text_input("E-mail")
                new_username = st.text_input("Nome de Usuário (Login)")
                new_password = st.text_input("Senha", type="password")
                new_password_repeat = st.text_input("Repetir Senha", type="password")

                submitted = st.form_submit_button("Criar Conta")

            if submitted:
                LoginUI._handle_registration(
                    auth_config, 
                    new_name, 
                    new_email, 
                    new_username, 
                    new_password, 
                    new_password_repeat
                )

        except Exception as e:
            st.error(f"Erro ao processar registro: {e}")

    @staticmethod
    def _handle_registration(
        auth_config: dict[str, Any], 
        name: str, 
        email: str, 
        username: str, 
        password: str, 
        password_repeat: str
    ) -> None:
        """Processa a lógica de registro."""
        # 1. Validações Básicas
        if not (name and email and username and password):
            st.error("Todos os campos são obrigatórios.")
            return
        if password != password_repeat:
            st.error("As senhas não coincidem.")
            return
        if len(password) < 6:
            st.error("A senha deve ter no mínimo 6 caracteres.")
            return
        if username in auth_config["credentials"]["usernames"]:
            st.error("Este nome de usuário já existe.")
            return

        # 2. Sucesso! Gerar Hash e Salvar
        hashed_password = stauth.Hasher([password]).generate()[0]

        # Estrutura do usuário no YAML
        new_user_data = {
            "name": name,
            "email": email,
            "password": hashed_password,
        }

        # Atualiza dict em memória
        auth_config["credentials"]["usernames"][username] = new_user_data

        # Persiste no disco
        with open("data/users.yaml", "w") as file:
            yaml.dump(auth_config, file, default_flow_style=False)

        # 3. Auto-Login
        st.session_state["authentication_status"] = True
        st.session_state["name"] = name
        st.session_state["username"] = username
        
        st.success("Conta criada! Redirecionando...")
        st.rerun()
