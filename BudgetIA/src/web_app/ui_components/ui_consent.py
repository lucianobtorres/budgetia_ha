# src/web_app/ui_components/ui_consent.py
import streamlit as st

from core.google_auth_service import GoogleAuthService
from web_app.onboarding_manager import OnboardingManager, OnboardingState


def render(manager: OnboardingManager, auth_service: GoogleAuthService) -> None:
    """
    Renderiza a tela de consentimento para habilitar os recursos de back-end.
    """

    # Pega os dados do arquivo que salvamos no session_state
    try:
        file_info = st.session_state.selected_google_file
        file_name = file_info["name"]
        file_id = file_info["id"]
    except (AttributeError, KeyError):
        st.error("Erro: Informações do arquivo selecionado não encontradas.")
        st.button("Voltar")
        st.stop()

    st.set_page_config(layout="centered")
    # st.image("assets/logo.png", width=100)  # (Assumindo que você tenha um logo)
    st.title("Habilite os Superpoderes do BudgetIA! 🚀")

    st.markdown(f"Você selecionou a planilha: **{file_name}**.")
    st.markdown("""
    Para que nossos assistentes proativos (como o **Bot do Telegram** e o **Agendador de Insights**) 
    possam analisar suas finanças e ajudá-lo 24h por dia, nosso sistema precisa de 
    permissão de **Leitor** na sua planilha.

    **Esta é uma escolha sua:**
    """)

    # --- O TEXTO CATIVANTE (Seu Insight) ---
    st.info(
        """
    **Modo Proativo (Recomendado):**
    Permite que o BudgetIA (nosso assistente "robô") leia sua planilha 
    mesmo quando você estiver offline. Isso habilita:
    * Consultas e registros via Telegram.
    * Análises agendadas e alertas proativos.
    * (Futuramente) Integrações com OpenFinance.
    
    **Modo Somente Web:**
    O app só funcionará enquanto esta aba do navegador estiver aberta. 
    Os recursos de back-end (Bot, Scheduler) ficarão desabilitados.
    
    *Sua privacidade é nossa prioridade. Você pode revogar este acesso
    a qualquer momento na sua tela de "Perfil".*
    """,
        icon="🛡️",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Sim, habilitar Modo Proativo", use_container_width=True, type="primary"
        ):
            with st.spinner(f"Compartilhando '{file_name}' com o assistente..."):
                success, msg = auth_service.share_file_with_service_account(file_id)

            if success:
                st.success(f"Recursos proativos habilitados! {msg}")
                # Avança para a próxima etapa (Geração de Estratégia)
                manager.set_state(OnboardingState.GENERATING_STRATEGY)
                st.rerun()
            else:
                st.error(f"Falha ao compartilhar: {msg}")

    with col2:
        if st.button("Não, usar Modo Somente Web", use_container_width=True):
            st.warning("Recursos proativos desabilitados.")
            # Avança para a próxima etapa (Geração de Estratégia)
            manager.set_state(OnboardingState.GENERATING_STRATEGY)
            st.rerun()

    st.stop()
