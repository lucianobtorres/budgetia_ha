# src/web_app/ui_components/ui_file_selection.py
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import streamlit as st

from config import DATA_DIR
from web_app.onboarding_manager import OnboardingManager


def render(
    manager: OnboardingManager, validation_callback: Callable[[str], Any]
) -> None:
    """Renderiza a tela de seleção/criação de planilha."""
    st.title("💰 Bem-vindo ao BudgetIA!")
    st.info("Para começar, precisamos de uma planilha.")

    col1, col2 = st.columns(2)
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

    st.stop()
