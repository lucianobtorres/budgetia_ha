import json

import streamlit as st

from initialization.onboarding.orchestrator import OnboardingOrchestrator
from initialization.onboarding.state_machine import OnboardingState


def render(orchestrator: OnboardingOrchestrator) -> None:
    """
    Renderiza a interface de onboarding conversacional (Hybrid UI).
    """
    st.title("Bem-vindo ao BudgetIA! 🚀")

    query_params = st.query_params
    auth_code = query_params.get("code")
    state_param = query_params.get("state")  # ← NOVO: Pega o state do OAuth

    # DEBUG: Log de todos os query params
    print(f"[DEBUG CALLBACK] Query params presentes: {list(query_params.keys())}")
    print(f"[DEBUG CALLBACK] auth_code presente: {bool(auth_code)}")
    print(f"[DEBUG CALLBACK] state_param presente: {bool(state_param)}")
    if state_param:
        print(f"[DEBUG CALLBACK] state_param valor: {state_param[:100]}...")  # Primeiros 100 chars

    if auth_code:
        print(f"[OAUTH CALLBACK] Código OAuth detectado! Iniciando processamento...")
        
        # ✅ NOVO: Restaura estado do onboarding se presente
        if state_param:
            try:
                print(f"[OAUTH CALLBACK] Tentando decodificar state...")
                state_data = json.loads(state_param)
                saved_onboarding_state = state_data.get("onboarding_state")
                print(f"[OAUTH CALLBACK] State decodificado: {state_data}")
                
                if saved_onboarding_state:
                    # Força o orchestrator a voltar para o estado correto
                    print(f"[OAUTH CALLBACK] ANTES - Estado atual: {orchestrator.get_current_state().name}")
                    orchestrator.state_machine.transition_to(OnboardingState[saved_onboarding_state])
                    print(f"[OAUTH CALLBACK] DEPOIS - Estado restaurado: {orchestrator.get_current_state().name}")
                else:
                    print(f"[OAUTH CALLBACK] AVISO: state_param presente mas sem 'onboarding_state'")
            except Exception as e:
                print(f"[OAUTH CALLBACK] ERRO ao restaurar estado: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[OAUTH CALLBACK] AVISO: Nenhum state_param no callback - estado não será restaurado")
        
        # Inicializa mensagens se ainda não existir (necessário para callback)
        if "onboarding_messages" not in st.session_state:
            st.session_state.onboarding_messages = []
        
        # Chama orchestrator para fazer o token exchange
        st.session_state.onboarding_messages.append({
            "role": "user",
            "content": f"✅ Autenticação concluída",
        })

        # ✅ FIX: Ao invés de "autenticação concluída" (que o handler não reconhece),
        # simulamos que o usuário clicou em "Google Sheets" novamente.
        # Assim o handler detecta os tokens e mostra a lista de arquivos automaticamente.
        # IMPORTANTE: Passamos o redirect_uri para que a troca de tokens funcione
        response = orchestrator.process_user_input(
            "Google Sheets",  # ← Simula o clique original
            extra_context={
                "google_auth_code": auth_code, 
                "redirect_uri": "http://localhost:8501" # ← Garante validacao correta do token
            }
        )

        st.session_state.onboarding_messages.append(
            {"role": "assistant", "content": response}
        )
        
        # Limpa os query params
        print(f"[OAUTH CALLBACK] Limpando query params e executando rerun...")
        st.query_params.clear()
        st.rerun()  # Reroda após o callback
        return

    # 1. Inicializa session state para mensagens
    if "onboarding_messages" not in st.session_state:
        st.session_state.onboarding_messages = []

    # 2. Se é a primeira vez (sem mensagens), mostra boas-vindas
    if len(st.session_state.onboarding_messages) == 0:
        # Get dynamic initial message from orchestrator (if available)
        welcome_msg = orchestrator.get_initial_message()
        if not welcome_msg:
            # Fallback if no auto-greeting available
            welcome_msg = "Olá! 👋 Pronto para começar?"
        
        print(f"[UI ONBOARDING] Initial message: {welcome_msg[:100]}...")  # Log first 100 chars
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
    current_state = orchestrator.get_current_state()

    if (
        current_state == OnboardingState.TRANSLATION_REVIEW
        and orchestrator._translation_result is None
    ):
        # O Streamlit travaria aqui. Usamos o spinner para dar feedback visual.
        with st.spinner(
            "🧠 Analisando sua planilha e gerando estratégia de mapeamento... Isso pode levar alguns segundos..."
        ):
            # Chama o Orchestrator com um input de gatilho para executar o bloco longo
            # no _handle_translation_review.
            response = orchestrator.process_user_input(
                "iniciar análise", extra_context={}
            )

        # A resposta (do Agente Conversacional) é adicionada ao histórico.
        st.session_state.onboarding_messages.append(
            {"role": "assistant", "content": response}
        )
        # Reroda para que o input e botões sejam desbloqueados com o novo estado de _translation_result
        st.rerun()
        return

    is_analysis_pending_final = (
        current_state == OnboardingState.TRANSLATION_REVIEW
        and orchestrator._translation_result is None
    )
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
        st.info(
            "Vamos te redirecionar para o Google para autorizar o acesso à leitura da sua planilha. Seus dados ficam seguros e NADA é alterado sem sua permissão! 🔒"
        )

        google_auth_service = orchestrator.get_google_auth_service()
        # ✅ NOVO: Passa o estado atual para preservar durante o redirect OAuth
        current_state_name = orchestrator.get_current_state().name
        
        # Define a URI explícita para o Streamlit (fixa aqui, mas poderia vir de config)
        streamlit_redirect_uri = "http://localhost:8501"
        
        print(f"[DEBUG AUTH URL] Gerando URL OAuth com estado: {current_state_name} e URI: {streamlit_redirect_uri}")
        
        auth_url = google_auth_service.generate_authorization_url(
            current_onboarding_state=current_state_name,
            redirect_uri=streamlit_redirect_uri # ← Garante que o serviço use a porta 8501
        )
        
        print(f"[DEBUG AUTH URL] URL gerada (primeiros 200 chars): {auth_url[:200]}...")
        if "state" in auth_url:
            print(f"[DEBUG AUTH URL] ✅ Parâmetro 'state' PRESENTE na URL")
        else:
            print(f"[DEBUG AUTH URL] ⚠️ Parâmetro 'state' AUSENTE na URL!")

        # 1. Marca o estado de progresso
        # Isso garante que no próximo rerun (após o Google), o callback seja detectado.
        # Definir a session_state aqui deve ser seguro, pois estamos no bloco da UI action.
        st.session_state["auth_in_progress"] = True

        # 2. Usa o link_button que direciona o navegador para o URL externo
        # O link_button não dispara um rerun interno como o st.button, ele redireciona o browser.
        st.link_button(
            "🔗 Abrir Conexão Google", url=auth_url
        )

        st.markdown(
            """
            <p style='font-size: small; margin-top: 10px;'>
            Ao clicar acima, você será levado para o Google para autorizar.
            Volte para esta tela para continuar o processo.
            </p>
        """,
            unsafe_allow_html=True,
        )

    elif ui_action_needed == "show_file_selection":
        st.markdown("---")
        st.subheader("✅ Google Conectado! Escolha sua Planilha.")
        st.info(
            "Selecione qual arquivo do seu Drive o BudgetIA deve monitorar. Vamos apenas ler (por enquanto), prometo! 😉"
        )

        google_auth_service = orchestrator.get_google_auth_service()

        # 1. Lista os arquivos
        try:
            files_list = google_auth_service.list_google_drive_files()
        except Exception as e:
            st.error(f"Erro ao listar arquivos. Tente novamente: {e}")
            st.warning(
                "Se o erro persistir, o token pode ter expirado. Tente refazer a conexão."
            )
            return

        options = {
            file["name"]: {"url": file["webViewLink"], "id": file["id"]}
            for file in files_list
        }

        file_names = list(options.keys())

        if not file_names:
            st.warning(
                "Nenhuma planilha encontrada no seu Drive que possamos ler (.xlsx ou Google Sheets)."
            )
            return

        # 2. Dropdown de seleção
        selected_file_name = st.selectbox(
            "Selecione o arquivo da Planilha Mestra:",
            file_names,
            key="google_file_selector",
        )

        # 3. Botão de confirmação
        if st.button(
            "Confirmar Planilha Selecionada",
            key="confirm_google_file",
        ):
            selected_url = options[selected_file_name]["url"]
            file_id = options[selected_file_name]["id"]

            # --- PASSO CRÍTICO: Compartilhar com Service Account (o "robô" back-end) ---
            with st.spinner("Configurando permissões de acesso ao back-end..."):
                success, share_msg = (
                    google_auth_service.share_file_with_service_account(file_id)
                )

            st.session_state.onboarding_messages.append(
                {
                    "role": "assistant",
                    "content": f"Configuração de permissões: {share_msg}",
                }
            )

            if not success:
                # Se falhar o compartilhamento, não conclui o fluxo.
                st.error(
                    "Falha ao configurar as permissões de leitura. Por favor, tente novamente ou escolha outro arquivo."
                )
                st.rerun()

            # 4. Envia a URL selecionada para o Orchestrator
            st.session_state.onboarding_messages.append(
                {
                    "role": "user",
                    "content": f"Planilha selecionada: {selected_file_name}",
                }
            )

            # Passa a URL selecionada para o Orchestrator (GoogleSheetsHandler.acquire)
            response = orchestrator.process_user_input(
                "seleção de planilha", extra_context={"google_file_url": selected_url}
            )

            st.session_state.onboarding_messages.append(
                {"role": "assistant", "content": response}
            )
            st.rerun()

    # 6. Input de texto (sempre disponível)
    if prompt := st.chat_input(
        "Digite sua resposta ou dúvida...", disabled=is_analysis_pending_final
    ):
        st.session_state.onboarding_messages.append({"role": "user", "content": prompt})

        # Detecta se o input é um comando de transição para iniciar a análise E a análise não foi feita.
        is_analysis_trigger = current_state == OnboardingState.TRANSLATION_REVIEW and (
            prompt.lower().strip()
            in [
                "continuar",
                "avançar",
                "próximo",
                "ok",
                "tudo certo",
                "confirmar",
                "começar a usar",
                "comecar a usar",
                "iniciar análise da planilha",
            ]
        )

        # Se for o gatilho da análise e a análise está pendente, mostra o spinner (e executa a tarefa longa)
        if is_analysis_trigger and is_analysis_pending_final:
            with st.spinner(
                "🧠 Analisando sua planilha e gerando estratégia de mapeamento... Isso pode levar alguns segundos..."
            ):
                response = orchestrator.process_user_input(prompt)
        else:
            # Caso contrário, executa a chamada normal com spinner
            with st.spinner("Processando..."):
                response = orchestrator.process_user_input(prompt)

        st.session_state.onboarding_messages.append(
            {"role": "assistant", "content": response}
        )
        st.rerun()
        return

    # 7. Botões de ação rápida (somente se NÃO houver UI action pendente)
    if not ui_action_needed and not is_analysis_pending_final:
        options = orchestrator.get_ui_options()
        if options:
            st.markdown("---")
            st.markdown("**Atalhos rápidos:**")
            cols = st.columns(len(options))
            for idx, option in enumerate(options):
                if cols[idx].button(
                    option, key=f"btn_{option}"
                ):
                    st.session_state.onboarding_messages.append(
                        {"role": "user", "content": option}
                    )
                    if (
                        current_state == OnboardingState.TRANSLATION_REVIEW
                        and option.strip() in orchestrator.get_ui_options()
                    ):
                        # Se o botão é um dos que inicia a análise, usamos o spinner
                        with st.spinner("🧠 Analisando sua planilha..."):
                            response = orchestrator.process_user_input(option)
                    else:
                        with st.spinner("Processando..."):
                            response = orchestrator.process_user_input(option)

                    st.session_state.onboarding_messages.append(
                        {"role": "assistant", "content": response}
                    )
                    st.rerun()
                    return
