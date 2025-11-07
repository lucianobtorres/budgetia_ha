# src/web_app/ui_components/ui_profile_setup.py
import time

import streamlit as st

from core.agent_runner_interface import AgentRunner
from finance.planilha_manager import PlanilhaManager
from web_app.onboarding_manager import OnboardingManager


def render(
    manager: OnboardingManager, agent_runner: AgentRunner, plan_manager: PlanilhaManager
) -> None:
    """Renderiza o chat de onboarding do perfil."""
    st.header("✨ Configurando seu Perfil Financeiro")
    st.warning("Seu perfil financeiro parece incompleto...")
    st.markdown(
        "Converse com a IA abaixo para configurar sua **Renda Mensal Média** e **Principal Objetivo Financeiro**:"
    )

    if "onboarding_messages" not in st.session_state:
        st.session_state.onboarding_messages = [
            {
                "role": "assistant",
                "content": "Olá! Para começar, qual sua Renda Mensal Média?",
            }
        ]

    for message in st.session_state.onboarding_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Responda à IA...", key="onboarding_input"):
        st.session_state.onboarding_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analisando e salvando..."):
                output = manager.process_profile_input(prompt, agent_runner)

                st.markdown(output)
                st.session_state.onboarding_messages.append(
                    {"role": "assistant", "content": output}
                )

                # Verifica DEPOIS da IA rodar
                if manager.verificar_perfil_preenchido(plan_manager):
                    st.success("Perfil configurado! Redirecionando...")
                    time.sleep(2)
                    st.rerun()

    st.stop()
