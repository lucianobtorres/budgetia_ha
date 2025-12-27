# src/web_app/ui_components/ui_file_selection.py
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import streamlit as st

from config import DATA_DIR
from core.google_auth_service import GoogleAuthService
from initialization.onboarding_manager import OnboardingManager


def render(
    manager: OnboardingManager, validation_callback: Callable[[str], Any]
) -> None:
    """Renderiza a tela de seleção/criação de planilha."""
    st.title("💰 Bem-vindo ao BudgetIA!")
    st.info("Para começar, precisamos de uma planilha.")

    auth_service = GoogleAuthService(manager.config_service)

    col1, col2, col3 = st.columns(3)

    with col1:  # Criar Nova
        st.subheader("🚀 Criar Nova Planilha Mestra")
        default_path = str(Path(DATA_DIR) / "planilha_mestra.xlsx")
        novo_path_input = st.text_input("Nome e local:", default_path, key="novo_path")

        if st.button("Criar e Usar localmente", key="criar_nova"):
            success, message = manager.create_new_planilha(
                novo_path_input, validation_callback
            )
            if success:
                st.success(message)
                time.sleep(1)
                st.rerun()
            else:
                st.error(message)

    with col2:  # Usar Existente
        st.subheader("📂 Usar Minha Planilha Existente")
        uploaded_file = st.file_uploader(
            "Carregar (.xlsx)", type=["xlsx"], key="uploader"
        )
        if uploaded_file is not None:
            success, message = manager.handle_uploaded_planilha(uploaded_file, DATA_DIR)
            if success:
                st.success(message)
                time.sleep(1)
            else:
                st.error(message)
            st.rerun()  # Vai para GENERATING_STRATEGY

        st.write("--- OU ---")
        path_input = st.text_input(
            "Insira o caminho completo:",
            key="path_input",
            placeholder="C:\\...\\financas.xlsx OU https://docs.google.com/...",
        )
        if st.button("Usar por Caminho ou link", key="usar_path"):
            if not path_input:
                st.warning("O campo não pode estar vazio.")
            else:
                success, message = manager.set_planilha_from_path(path_input)
                if success:
                    st.success(message)
                    time.sleep(1)
                else:
                    st.error(message)
                st.rerun()  # Vai para GENERATING_STRATEGY

    with col3:
        st.subheader("🌐 Opção C: Selecionar do Google")

        # Verifica se o usuário JÁ conectou o Google
        auth_service = GoogleAuthService(manager.config_service)
        user_creds = auth_service.get_user_credentials()

        if user_creds is None:
            # --- CASO 1: NÃO LOGADO (Seu Insight) ---
            st.markdown("**A forma mais fácil e recomendada.**")
            st.caption(
                "Você fará login com sua conta Google e selecionará seu arquivo."
            )
            try:
                auth_url = auth_service.generate_authorization_url()
                st.link_button(
                    "Fazer login com o Google", auth_url, use_container_width=True
                )
            except Exception as e:
                st.error(f"Não foi possível gerar o link de login: {e}")
                st.caption("Verifique se as chaves GOOGLE_OAUTH estão no seu .env")

        else:
            # --- CASO 2: JÁ LOGADO (Seu Insight) ---
            st.success("Conectado ao Google!")
            st.caption("Selecione sua Planilha Mestra na lista abaixo.")

            files_list = []
            try:
                with st.spinner("Buscando seus arquivos no Google Drive..."):
                    files_list = auth_service.list_google_drive_files()
            except Exception as e:
                st.error(f"Erro ao buscar arquivos: {e}")

            if files_list:
                file_options = {
                    f"{file['name']}": (file["id"], file["name"], file["webViewLink"])
                    for file in files_list
                }
                options_list = ["Selecione um arquivo..."] + list(file_options.keys())

                selected_file_name = st.selectbox(
                    "Seus arquivos Google Sheets e Excel:",
                    options=options_list,
                    index=0,
                )

                if selected_file_name != "Selecione um arquivo...":
                    file_id, file_name, file_url = file_options[selected_file_name]

                    # --- LÓGICA CORRIGIDA (DIVISÃO DE RESPONSABILIDADES) ---

                    # 1. Avisa o Manager (Lógica de Negócio)
                    manager.set_google_file_selection(file_url)

                    # 2. Salva dados para a próxima TELA (Lógica de UI)
                    st.session_state.selected_google_file = {
                        "id": file_id,
                        "name": file_name,
                        "url": file_url,
                    }

                    # 3. Força a UI a recarregar para o novo estado
                    st.rerun()

    st.stop()
