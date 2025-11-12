# src/web_app/ui_components/ui_profile_setup.py
import time

import streamlit as st

# --- NOVOS IMPORTS ---
from app.chat_service import ChatService

# Remover 'AgentRunner' - não falamos mais com ele diretamente
# --- FIM NOVOS IMPORTS ---
from finance.planilha_manager import PlanilhaManager
from web_app.onboarding_manager import OnboardingManager


def render(
    manager: OnboardingManager,
    chat_service: ChatService,  # Recebe o ChatService
    plan_manager: PlanilhaManager,
) -> None:
    """Renderiza o chat de onboarding do perfil."""
    st.header("✨ Configurando seu Perfil Financeiro")
    st.warning("Seu perfil financeiro parece incompleto...")
    st.markdown(
        "Converse com a IA abaixo para configurar sua **Renda Mensal Média** e **Principal Objetivo Financeiro**:"
    )

    # Adiciona a primeira mensagem (agora via service)
    chat_service.add_first_message("Olá! Para começar, qual sua Renda Mensal Média?")

    # Exibe o histórico (lido do service)
    for message in chat_service.get_history():
        with st.chat_message(message["role"]):
            st.write(message["content"])  # Usando st.write como pedido

    if prompt := st.chat_input("Responda à IA...", key="onboarding_input"):
        # Adiciona e exibe a mensagem do usuário IMEDIATAMENTE
        # (O Service fará isso, mas para UX, exibimos aqui também)
        with st.chat_message("user"):
            st.write(prompt)

        # Chama a IA (via service)
        with st.chat_message("assistant"):
            with st.spinner("Analisando e salvando..."):
                # Este é o prompt guiado que o OnboardingManager usava
                profile_prompt_template = (
                    "O usuário respondeu: '{prompt}'.\n"
                    "Seu ÚNICO objetivo é extrair DADOS DE PERFIL (especificamente 'Renda Mensal Média' ou 'Principal Objetivo') desta resposta. "
                    "Se você extrair um dado, use a ferramenta 'coletar_perfil_usuario' IMEDIATAMENTE para salvar o par 'campo' e 'valor' (ex: campo='Renda Mensal Média', valor=5000). "
                    "Após salvar, confirme o que salvou e faça a próxima pergunta (se a Renda foi dada, pergunte o Objetivo; se o Objetivo foi dado, pergunte a Renda). "
                    "Se você não conseguir extrair um dado válido, peça educadamente pela informação novamente (Renda ou Objetivo)."
                    "NÃO use outras ferramentas. NÃO responda a perguntas aleatórias. Foque 100% em preencher o perfil."
                )

                # O Service agora lida com a lógica
                # O 'handle_profile_message' salva o 'prompt', chama a IA, e salva a 'response'
                output = chat_service.handle_profile_message(
                    prompt, profile_prompt_template
                )

                # Não precisamos mais exibir 'output' aqui, o rerun() vai

                # Verifica DEPOIS da IA rodar
                if manager.verificar_perfil_preenchido(plan_manager):
                    st.success("Perfil configurado! Redirecionando...")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.rerun()

    st.stop()
