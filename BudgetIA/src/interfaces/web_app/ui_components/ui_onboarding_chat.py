# Em: src/web_app/ui_components/ui_onboarding_chat.py

import json
import streamlit as st
from interfaces.web_app.api_client import BudgetAPIClient
from core.exceptions import BudgetException

# Note: We still import the ENUM for comparison, but not the Orchestrator logic
from initialization.onboarding.state_machine import OnboardingState

def render(api_client: BudgetAPIClient) -> None:
    """
    Renderiza a interface de onboarding conversacional (API-Driven UI).
    Agora o Frontend é 'burro' e pergunta tudo para a API.
    """
    try:
        col1, col2 = st.columns([0.2, 0.8])
        with col1:
             st.image("src/assets/logo.png", width=80)
        with col2:
             st.title("BudgetIA")
    except Exception:
        st.title("Bem-vindo ao BudgetIA! 🚀")

    # --- 1. Sincronização de Estado (Polling inicial) ---
    state_data = {}
    try:
        state_data = api_client.get_onboarding_state()
    except BudgetException:
        # Silently fail on init poll, simpler
        pass

    current_state_name = state_data.get("state", "WELCOME")
    is_analysis_complete = state_data.get("is_analysis_complete", False)
    
    # Converte string para Enum para facilitar comparações de UI logic
    try:
        current_state = OnboardingState[current_state_name]
    except KeyError:
        current_state = OnboardingState.WELCOME

    # --- 2. OAuth Callback Handling ---
    query_params = st.query_params
    auth_code = query_params.get("code")
    
    if auth_code:
        st.info("🔄 Processando autenticação com Google...")
        
        # Envia código para API processar
        # IMPORTANTE: Mesma URI usada no redirect do Google
        redirect_uri = "http://localhost:8501" 
        
        resp = {}
        msg_content = "Conectado com sucesso!"
        try:
            resp = api_client.send_google_auth_code(auth_code, redirect_uri)
            msg_content = resp.get("message", "Conectado com sucesso!")
        except BudgetException as e:
            msg_content = f"❌ Erro na autenticação: {e}"
        
        # Adiciona resposta ao histórico local para feedback
        if "onboarding_messages" not in st.session_state:
            st.session_state.onboarding_messages = []
            
        st.session_state.onboarding_messages.append({
            "role": "user",
            "content": f"✅ Autenticação Google concluída"
        })
        st.session_state.onboarding_messages.append({
            "role": "assistant", 
            "content": msg_content
        })
        
        # Limpa URL e recarrega
        st.query_params.clear()
        st.rerun()


    # --- 3. Inicialização de Chat ---
    if "onboarding_messages" not in st.session_state:
        st.session_state.onboarding_messages = []

    # Se vazio e temos uma mensagem inicial do servidor, exibe
    if not st.session_state.onboarding_messages and state_data:
        initial_msg = state_data.get("initial_message")
        if initial_msg:
             st.session_state.onboarding_messages.append({
                "role": "assistant",
                "content": initial_msg
            })
        elif current_state == OnboardingState.WELCOME:
             # Fallback client-side se servidor não mandou nada (raro)
             st.session_state.onboarding_messages.append({
                "role": "assistant",
                "content": "Olá! 👋 Pronto para começar a organizar suas finanças?"
            })
    
    # Fallback se a API falhou totalmente
    if not st.session_state.onboarding_messages and not state_data:
        st.warning("⚠️ Parece que o servidor está offline. Tente recarregar.")

    # --- 4. Renderização do Chat ---
    # Exibe histórico
    for msg in st.session_state.onboarding_messages:
        content = msg["content"]
        # Limpa tags internas de UI_ACTION se aparecerem
        if "[UI_ACTION:" in content and "]" in content:
            # Mostra só a parte do texto
            parts = content.split("]")
            if len(parts) > 1:
                content = parts[1].strip()
        
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(content)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.write(content)

    # --- 5. Detecção de Ação de UI (Baseada na última msg do bot) ---
    ui_action_needed = None
    if st.session_state.onboarding_messages:
        last_msg = st.session_state.onboarding_messages[-1]
        if last_msg["role"] == "assistant" and "[UI_ACTION:" in last_msg["content"]:
             # Extrai comando: [UI_ACTION:comando]
             start = last_msg["content"].find("[UI_ACTION:") + len("[UI_ACTION:")
             end = last_msg["content"].find("]", start)
             if end != -1:
                 ui_action_needed = last_msg["content"][start:end]

    # --- 6. Lógica Específica de Estado ---
    
    # Caso especial: Spinner de Análise
    # Se estamos em TRANSLATION_REVIEW mas a análise AINDA NÃO terminou (flag do backend)
    # E não estamos esperando uma ação de UI (ex: erro)
    if current_state == OnboardingState.TRANSLATION_REVIEW and not is_analysis_complete:
        if not ui_action_needed: # Se tiver UI action (ex: erro), não roda spinner
             with st.spinner("🧠 Analisando sua planilha no servidor... Isso pode levar alguns segundos..."):
                 try:
                     resp = api_client.send_onboarding_message("verificar análise")
                     st.session_state.onboarding_messages.append({"role": "assistant", "content": resp["message"]})
                     st.rerun()
                 except BudgetException as e:
                     st.error(f"Erro ao verificar análise: {e}")
             return

    # --- 7. Componentes de UI Dinâmicos (File Uploader, Buttons) ---
    
    if ui_action_needed == "show_file_uploader":
        st.markdown("---")
        st.subheader("📤 Envie seu arquivo Excel")
        uploaded_file = st.file_uploader(
            "Escolha seu arquivo", type=["xlsx", "csv"], key="uploaded_spreadsheet"
        )
        
        if uploaded_file:
            st.session_state.onboarding_messages.append(
                {"role": "user", "content": f"📎 Arquivo enviado: {uploaded_file.name}"}
            )
            with st.spinner("Enviando arquivo para o servidor..."):
                try:
                    resp = api_client.upload_onboarding_file(uploaded_file, uploaded_file.name)
                    st.session_state.onboarding_messages.append(
                        {"role": "assistant", "content": resp.get("message", "Upload concluído")}
                    )
                except BudgetException as e:
                    st.session_state.onboarding_messages.append(
                         {"role": "assistant", "content": f"❌ Falha no upload: {e}"}
                    )
            
            st.session_state.uploaded_file = None # Limpa para não re-enviar
            st.rerun()

    elif ui_action_needed == "show_google_oauth":
        st.markdown("---")
        st.subheader("☁️ Conectar Google Sheets")
        st.info("Vamos te redirecionar para o Google com segurança! 🔒")
        
        redirect_uri = "http://localhost:8501"
        auth_url = api_client.get_google_auth_url(redirect_uri)
        
        if auth_url:
            st.link_button("🔗 Abrir Conexão Google", url=auth_url)
        else:
            st.error("Erro ao gerar link de autenticação.")

    elif ui_action_needed == "show_file_selection":
        st.markdown("---")
        st.subheader("✅ Google Conectado! Escolha sua Planilha.")
        
        files_list = st.session_state.get("last_google_files_list", [])
        
        if not files_list:
            st.warning("⚠️ Não encontrei a lista de arquivos. Sua sessão pode ter expirado.")
            if st.button("🔄 Reconectar Google / Trocar Conta"):
                st.session_state.onboarding_messages.append({"role": "user", "content": "Trocar conta"})
                with st.spinner("Reiniciando conexão..."):
                    try:
                        resp = api_client.send_onboarding_message("Trocar conta")
                        st.session_state.onboarding_messages.append({"role": "assistant", "content": resp["message"]})
                    except BudgetException as e:
                        st.session_state.onboarding_messages.append({"role": "assistant", "content": f"❌ Erro: {e}"})
                st.rerun()
        else:
            options = {f["name"]: f["url"] for f in files_list}
            selected_name = st.selectbox("Selecione o arquivo:", list(options.keys()))
            
            if st.button("Confirmar Seleção"):
                url = options[selected_name]
                st.session_state.onboarding_messages.append({"role": "user", "content": f"Selecionei: {selected_name}"})
                
                # Envia URL extra context via chat
                with st.spinner("Conectando planilha..."):
                    try:
                        resp = api_client.send_onboarding_message("seleção de planilha", extra_context={"google_file_url": url})
                        st.session_state.onboarding_messages.append(
                            {"role": "assistant", "content": resp["message"]}
                        )
                    except BudgetException as e:
                        st.session_state.onboarding_messages.append(
                            {"role": "assistant", "content": f"❌ Erro ao conectar: {e}"}
                        )
                
                st.rerun()

    # --- 8. Input de Chat ---
    
    # Desabilita input se análise pendente
    input_disabled = (current_state == OnboardingState.TRANSLATION_REVIEW and not is_analysis_complete)
    
    if prompt := st.chat_input("Digite sua resposta...", disabled=input_disabled):
        st.session_state.onboarding_messages.append({"role": "user", "content": prompt})
        with st.spinner("Enviando..."):
            try:
                resp = api_client.send_onboarding_message(prompt)
                
                # Guarda metadados úteis
                if resp.get("google_files_list"):
                    st.session_state["last_google_files_list"] = resp["google_files_list"]

                st.session_state.onboarding_messages.append({"role": "assistant", "content": resp["message"]})
            except BudgetException as e:
                st.session_state.onboarding_messages.append({"role": "assistant", "content": f"❌ Erro de comunicação: {e}"})
        
        st.rerun()

    # --- 9. Botões de Sugestão (Chips) ---
    if not ui_action_needed and not input_disabled:
        options = state_data.get("ui_options", [])
        if options:
            st.markdown("---")
            cols = st.columns(len(options))
            for idx, option in enumerate(options):
                if cols[idx].button(option, key=f"btn_{idx}"):
                    st.session_state.onboarding_messages.append({"role": "user", "content": option})
                    with st.spinner("Processando..."):
                        try:
                            resp = api_client.send_onboarding_message(option)
                            
                            if resp.get("google_files_list"):
                                st.session_state["last_google_files_list"] = resp["google_files_list"]
                                
                            st.session_state.onboarding_messages.append({"role": "assistant", "content": resp["message"]})
                        except BudgetException as e:
                            st.session_state.onboarding_messages.append({"role": "assistant", "content": f"❌ Erro de comunicação: {e}"})

                    st.rerun()
