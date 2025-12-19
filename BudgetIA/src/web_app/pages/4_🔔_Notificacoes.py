import streamlit as st
from web_app.utils import initialize_session_auth

# Configuração da página
st.set_page_config(
    page_title="Central de Notificações - BudgetIA",
    page_icon="🔔",
    layout="wide"
)

# 1. Autenticação e Configuração
# 1. Autenticação e Configuração
# A função não recebe argumentos e retorna 4 valores
authenticated, username, config_service, llm_orchestrator = initialize_session_auth()

if not authenticated:
    st.warning("Por favor, faça login na página inicial.")
    st.stop()

# 2. Interface Principal
st.title("🔔 Central de Notificações")
st.markdown("---")

api_client = st.session_state.api_client

# Ações em massa
col_actions, col_space = st.columns([1, 4])
with col_actions:
    if st.button("Marcar Todas como Lidas", use_container_width=True):
        if api_client.mark_all_notifications_read():
            st.toast("Todas as notificações marcadas como lidas!", icon="✅")
            st.rerun()
        else:
            st.error("Erro ao atualizar notificações.")

# 3. Listagem
notifications = api_client.get_notifications(unread_only=True)

if not notifications:
    st.info("🎉 **Tudo limpo!** Você não tem novas notificações.")
    
    # Opção para ver histórico (se implementado endpoints de 'all')
    # st.markdown("Você está em dia com suas finanças.")
else:
    for notif in notifications:
        # Define ícone e cor por prioridade
        priority = notif.get("priority", "medium")
        if priority == "high":
            icon = "🚨"
            border_color = "red"
        elif priority == "low":
            icon = "ℹ️"
            border_color = "blue"
        else:
            icon = "⚠️"
            border_color = "orange"
            
        with st.container(border=True):
            cols = st.columns([0.1, 0.6, 0.15, 0.15])
            
            with cols[0]:
                st.markdown(f"## {icon}")
            
            with cols[1]:
                st.markdown(f"**{notif.get('message')}**")
                st.caption(f"{notif.get('timestamp')} • {notif.get('category')}")
                
            with cols[2]:
                if st.button("Lida", key=f"read_{notif['id']}", use_container_width=True):
                    if api_client.mark_notification_read(notif["id"]):
                        st.rerun()
                    else:
                        st.error("Erro.")
            
            with cols[3]:
                if st.button("🗑️", key=f"del_{notif['id']}", use_container_width=True):
                    if api_client.delete_notification(notif["id"]):
                        st.rerun()
                    else:
                        st.error("Erro.")
