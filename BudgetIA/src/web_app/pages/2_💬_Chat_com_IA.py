# pages/2_💬_Chat_com_IA.py

import streamlit as st

try:
    from ..ui_components.common_ui import setup_page
except ImportError:
    from web_app.ui_components.common_ui import setup_page

plan_manager, agent_runner = setup_page(
    title="Converse com seu Mentor Financeiro", icon="💬"
)

llm_orchestrator = st.session_state.llm_orchestrator

# Inicializa o histórico de chat específico desta página no session_state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Exibe mensagens do histórico
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input(
    "Como posso te ajudar com suas finanças hoje? (Ex: Qual meu saldo?, Adicione despesa...)"
):
    # Adiciona e exibe a mensagem do usuário
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- CORREÇÃO DO BLOCO DA IA ---
    with st.chat_message("assistant"):
        with st.spinner("IA pensando..."):
            try:
                # --- CORREÇÃO: Usar .interagir() e passar o prompt como string ---
                # (Assumindo que seu agente 'IADeFinancas' usa a memória interna)
                output = agent_runner.interagir(prompt)

                st.markdown(output)

                # Tenta obter info do LLM
                llm_info = getattr(llm_orchestrator, "active_model_name", None)
                if llm_info:
                    st.caption(f"_Modelo: {llm_info}_")

                # Adiciona resposta da IA ao histórico
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": output}
                )

                st.rerun()

            except Exception as e:
                st.error(f"Ocorreu um erro ao comunicar com a IA: {e}")
                error_msg = f"Erro: {e}"
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": error_msg}
                )
                st.rerun()
