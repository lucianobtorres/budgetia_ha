import streamlit as st

from initialization.onboarding.orchestrator import OnboardingOrchestrator


def render(orchestrator: OnboardingOrchestrator):
    """
    Renderiza a interface de onboarding conversacional (Hybrid UI).
    """
    st.title("Bem-vindo ao BudgetIA! 🚀")

    # 1. Inicializa session state para mensagens
    if "onboarding_messages" not in st.session_state:
        st.session_state.onboarding_messages = []

    # 2. Se é a primeira vez (sem mensagens), mostra boas-vindas
    if len(st.session_state.onboarding_messages) == 0:
        welcome_msg = "Olá! 👋 Sou seu assistente pessoal de finanças. Vou te ajudar a configurar tudo de forma simples e rápida. Quando estiver pronto, clique em **Começar Agora**!"
        st.session_state.onboarding_messages.append(
            {"role": "assistant", "content": welcome_msg}
        )

    # 3. Exibe histórico de mensagens (filtra [UI_ACTION:...])
    for msg in st.session_state.onboarding_messages:
        content = msg["content"]

        # Remove [UI_ACTION:...] das mensagens exibidas
        if content.startswith("[UI_ACTION:"):
            # Extrai apenas a mensagem limpa
            if "]" in content:
                content = content.split("]", 1)[1].strip()

        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(content)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.write(content)

    # 4. Verifica se a última mensagem do assistente pede uma UI action
    ui_action_needed = None
    if st.session_state.onboarding_messages:
        last_msg = st.session_state.onboarding_messages[-1]
        if last_msg["role"] == "assistant" and last_msg["content"].startswith(
            "[UI_ACTION:"
        ):
            # Extrai a ação
            action_str = last_msg["content"].split("]")[0].replace("[UI_ACTION:", "")
            ui_action_needed = action_str

    # 5. Renderiza UI especial se necessário
    if ui_action_needed == "show_file_uploader":
        st.markdown("---")
        st.subheader("📤 Envie seu arquivo Excel")
        uploaded_file = st.file_uploader(
            "Escolha seu arquivo", type=["xlsx"], key="uploaded_spreadsheet"
        )

        if uploaded_file:
            # Processa o upload
            st.session_state.onboarding_messages.append(
                {"role": "user", "content": f"📎 Arquivo enviado: {uploaded_file.name}"}
            )

            # Chama orchestrator com o arquivo no contexto
            response = orchestrator.process_user_input(
                "upload de arquivo", extra_context={"uploaded_file": uploaded_file}
            )

            st.session_state.onboarding_messages.append(
                {"role": "assistant", "content": response}
            )
            st.rerun()

    elif ui_action_needed == "show_google_oauth":
        st.markdown("---")
        st.subheader("☁️ Conectar Google Sheets")
        st.info("Redirecionamento para autenticação Google seria iniciado aqui.")

        # PLACEHOLDER: Na implementação real, você chamaria GoogleAuthService aqui
        if st.button("🔗 Conectar minha conta Google", use_container_width=True):
            st.warning(
                "OAuth ainda não implementado nesta versão. Use 'Criar do Zero' ou 'Fazer Upload'."
            )

    # 6. Input de texto (sempre disponível)
    if prompt := st.chat_input("Digite sua resposta ou dúvida..."):
        st.session_state.onboarding_messages.append({"role": "user", "content": prompt})
        response = orchestrator.process_user_input(prompt)
        st.session_state.onboarding_messages.append(
            {"role": "assistant", "content": response}
        )
        st.rerun()

    # 7. Botões de ação rápida (somente se NÃO houver UI action pendente)
    if not ui_action_needed:
        options = orchestrator.get_ui_options()
        if options:
            st.markdown("---")
            st.markdown("**Atalhos rápidos:**")
            cols = st.columns(len(options))
            for idx, option in enumerate(options):
                if cols[idx].button(
                    option, key=f"btn_{option}", use_container_width=True
                ):
                    st.session_state.onboarding_messages.append(
                        {"role": "user", "content": option}
                    )
                    response = orchestrator.process_user_input(option)
                    st.session_state.onboarding_messages.append(
                        {"role": "assistant", "content": response}
                    )
                    st.rerun()
