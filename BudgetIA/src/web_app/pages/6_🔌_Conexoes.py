
import streamlit as st
import sys
import os

# Adiciona diretório src ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from web_app.utils import initialize_session_auth
from core.user_config_service import UserConfigService

def render_telegram_tab(config_service: UserConfigService, current_config: dict):
    st.header("Telegram Bot")
    st.markdown("""
    Receba notificações instantâneas sobre seus gastos e alertas diretamente no Telegram.
    
    **Como conectar:**
    1. Abra o Telegram e procure por [@BudgetIABot](https://t.me/BudgetIABot) (Exemplo).
    2. Clique em **Start**.
    3. O bot lhe enviará um código de **Chat ID**. Cole-o abaixo.
    """)
    
    current_chat_id = current_config.get("telegram_chat_id", "")
    new_chat_id = st.text_input("Seu Chat ID", value=current_chat_id, placeholder="Ex: 123456789")
    
    if st.button("Salvar Telegram"):
        config_service.save_comunicacao_field("telegram_chat_id", new_chat_id)
        # TODO: Enviar msg de teste real
        st.success("Configuração do Telegram salva!")
        
    st.info("Status: " + ("✅ Conectado" if new_chat_id else "❌ Não conectado"))

def render_whatsapp_tab(config_service: UserConfigService, current_config: dict):
    st.header("WhatsApp (Beta)")
    st.caption("🚀 Recurso Premium (Simulação)")
    
    st.markdown("""
    Receba interações ricas via WhatsApp.
    
    *Nota: Em ambiente de desenvolvimento, usamos o Sandbox da Twilio.*
    """)
    
    current_phone = current_config.get("whatsapp_phone", "")
    new_phone = st.text_input("Seu Número (com DDD)", value=current_phone, placeholder="Ex: +5511999999999")
    
    if st.button("Salvar WhatsApp"):
        config_service.save_comunicacao_field("whatsapp_phone", new_phone)
        st.success("Configuração do WhatsApp salva!")

def render_email_tab(config_service: UserConfigService, current_config: dict):
    st.header("E-mail")
    st.markdown("Receba relatórios semanais e alertas críticos.")
    
    current_email = current_config.get("email_address", "")
    new_email = st.text_input("Seu E-mail", value=current_email, placeholder="voce@exemplo.com")
    
    if st.button("Salvar E-mail"):
        config_service.save_comunicacao_field("email_address", new_email)
        st.success("E-mail salvo!")

def render_sms_tab(config_service: UserConfigService, current_config: dict):
    st.header("SMS (Mensagem de Texto)")
    st.caption("Último recurso para alertas críticos.")
    
    current_sms = current_config.get("sms_phone", "")
    new_sms = st.text_input("Número para SMS", value=current_sms, placeholder="+5511...")
    
    if st.button("Salvar SMS"):
        config_service.save_comunicacao_field("sms_phone", new_sms)
        st.success("Número SMS salvo!")

def main():
    st.set_page_config(page_title="Conexões", page_icon="🔌", layout="wide")

    # Autenticação
    is_logged_in, username, config_service, _ = initialize_session_auth()

    if not is_logged_in or not config_service:
        st.stop()
        
    st.title("🔌 Hub de Conexões")
    st.write("Gerencie os canais por onde o BudgetIA se comunica com você.")
    
    # Carregar config atual
    com_config = config_service.get_comunicacao_config()
    
    tabs = st.tabs(["Telegram", "WhatsApp", "E-mail", "SMS"])
    
    with tabs[0]:
        render_telegram_tab(config_service, com_config)
    
    with tabs[1]:
        render_whatsapp_tab(config_service, com_config)
        
    with tabs[2]:
        render_email_tab(config_service, com_config)
        
    with tabs[3]:
        render_sms_tab(config_service, com_config)

if __name__ == "__main__":
    main()
