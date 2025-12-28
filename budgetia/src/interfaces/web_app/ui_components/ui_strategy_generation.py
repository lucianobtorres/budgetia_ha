# src/web_app/ui_components/ui_strategy_generation.py
import time

import streamlit as st

from initialization.onboarding_manager import OnboardingManager


def render(manager: OnboardingManager) -> None:
    """Renderiza a tela de loading (spinner) enquanto a IA gera a estratégia."""
    st.title("💰 BudgetIA Analisando...")
    st.subheader("Sua planilha é única. Estou aprendendo a lê-la.")

    with st.spinner(
        "A IA está gerando e testando o código de tradução... (Isso pode levar um minuto)"
    ):
        # 1. Chama a função SÍNCRONA (pesada)
        success, message = manager._processar_planilha_customizada()

        # 2. Exibe o resultado
        if success:
            st.success(message)
        else:
            st.error(message)

        time.sleep(2)  # Dá tempo para o usuário ler

    # 3. Recarrega para o próximo estado (SETUP_COMPLETE ou FALLBACK)
    st.rerun()
    st.stop()
