
import time
import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import ColunasPerfil
from web_app.api_client import BudgetAPIClient
from web_app.utils import initialize_session_auth, create_excel_export_bytes
from core.google_auth_service import GoogleAuthService
from initialization.onboarding.orchestrator import OnboardingOrchestrator
from core.memory.memory_service import MemoryService
from app.notifications.rule_repository import RuleRepository

# --- Autenticação ---
is_logged_in, username, config_service, llm_orchestrator = initialize_session_auth()

if not is_logged_in:
    st.warning("Por favor, faça o login.")
    st.stop()

if "api_client" not in st.session_state:
    st.warning("API não conectada.")
    st.stop()

api_client: BudgetAPIClient = st.session_state.api_client

st.set_page_config(page_title="Perfil Financeiro", page_icon="👤", layout="wide")


def render_profile_editor_api(client: BudgetAPIClient) -> None:
    st.header("Seus Dados de Perfil", divider="blue")
    
    profile_data = client.get_profile()
    
    if not profile_data:
        st.info("Nenhum dado de perfil encontrado.")
        return

    df_perfil = pd.DataFrame(profile_data)
    
    st.info("Aqui estão os dados do seu perfil. O Chat com IA usa essas informações.")
    
    editor_key_perfil = "editor_perfil_api"
    
    edited_df_perfil = st.data_editor(
        df_perfil,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            ColunasPerfil.CAMPO: st.column_config.TextColumn(
                required=True, help="Nome do dado (Ex: Renda Mensal Média)."
            ),
            ColunasPerfil.VALOR: st.column_config.TextColumn(
                required=True, help="O valor correspondente ao campo."
            ),
            ColunasPerfil.OBS: st.column_config.TextColumn(help="Notas opcionais."),
        },
        hide_index=True,
        key=editor_key_perfil,
    )
    
    if not df_perfil.equals(edited_df_perfil):
        if st.button("Salvar Alterações no Perfil"):
            st.info("Enviando alterações...")
            try:
                # Converter para envio
                records = edited_df_perfil.to_dict(orient="records")
                if client.update_profile(records):
                    st.success("Perfil Financeiro atualizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Falha ao salvar via API.")
            except Exception as e:
                st.error(f"Erro: {e}")

def render_advanced_settings_local(
    config_service,
    auth_service: GoogleAuthService,
    api_client: BudgetAPIClient
) -> None:
    st.divider()
    st.header("Configurações Avançadas (Local)", divider="blue")
    
    planilha_path = config_service.get_planilha_path()
    is_google_sheet = planilha_path and "docs.google.com" in planilha_path
    
    with st.container(border=True):
        st.subheader("Conexões de Dados")
        st.info(f"**Planilha Ativa:** `{planilha_path}`")
        if is_google_sheet:
            st.markdown("**Modo Proativo (Bot & Scheduler)**")
            consent_dado = config_service.get_backend_consent()
            
            # ... Lógica do Google Auth ...
            # Mantendo simplificado aqui pois já temos acesso direto ao auth_service local
            help_text = "Permite que o BudgetIA (via Bot/Scheduler) leia e escreva na sua planilha 24/7, mesmo offline."
            if not auth_service.get_user_credentials():
                help_text = "Você precisa se conectar ao Google para gerenciar isso."
            
            novo_consentimento = st.toggle(
                "Habilitar recursos de back-end",
                value=consent_dado,
                help=help_text,
                disabled=(not auth_service.get_user_credentials()),
            )
            
            if novo_consentimento != consent_dado:
                # ... Logica de share/revoke mantida local por enquanto ...
                file_id = auth_service._extract_file_id_from_url(planilha_path)
                if novo_consentimento:
                    success, msg = auth_service.share_file_with_service_account(file_id)
                    if success:
                        config_service.save_backend_consent(True)
                        st.success(f"Habilitado! {msg}")
                        st.rerun()
                else:
                    success, msg = auth_service.revoke_file_sharing_from_service_account(file_id)
                    if success:
                        config_service.save_backend_consent(False)
                        st.success(f"Desabilitado! {msg}")
                        st.rerun()

    with st.container(border=True):
        st.subheader("Backup")
        # EXPORT via API
        excel_bytes, filename = api_client.export_excel_bytes()
        if excel_bytes:
            st.download_button(
                label="Baixar Cópia Local (Salvar Como...)",
                data=excel_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="download_backup_advanced",
            )
        else:
            st.warning("Não foi possível gerar backup via API.")

def render_danger_zone_local(
    orchestrator: OnboardingOrchestrator
) -> None:
    st.divider()
    st.subheader("Zona de Perigo")
    with st.expander("Zona de Perigo"):
        st.warning(
            "Isso irá desconectar sua planilha e reiniciar a configuração local."
        )
        
        if st.button(
            "Resetar e Configurar Nova Planilha",
            type="primary",
            use_container_width=True,
            key="reset_onboarding",
        ):
            orchestrator.reset_config()
            st.cache_resource.clear()
            for key in st.session_state.keys():
                if key not in ["authentication_status", "name", "username"]:
                    del st.session_state[key]
            st.success("Configuração reiniciada!")
            time.sleep(2)
            time.sleep(2)
            st.switch_page("💰_BudgetIA.py")

def render_mind_viewer(config_service) -> None:
    st.divider()
    st.header("🧠 Cérebro do Jarvis (Memória)", divider="violet")
    
    user_dir = config_service.get_user_dir()
    memory_service = MemoryService(user_dir)
    facts = memory_service._load_memory() # Acessando interno para view completa
    
    st.info("Estas são as coisas que eu aprendi sobre você durante nossas conversas.")
    
    if not facts:
        st.write("*Ainda não aprendi nada específico sobre suas preferências.*")
        return

    for i, fact in enumerate(facts):
        with st.container(border=True):
            cols = st.columns([0.8, 0.2])
            with cols[0]:
                st.markdown(f"**{fact.get('content')}**")
                st.caption(f"Aprendido: {fact.get('created_at')} via {fact.get('source', 'chat')}")
            with cols[1]:
                if st.button("Esquecer", key=f"del_fact_{i}"):
                    memory_service.forget_fact(fact.get('content'))
                    st.success("Esquecido!")
                    st.rerun()

def render_watchdog_viewer(config_service) -> None:
    st.divider()
    st.header("🐕 O Vigia (Regras Proativas)", divider="orange")
    
    user_dir = config_service.get_user_dir()
    repo = RuleRepository(user_dir)
    
    # Precisamos carregar o JSON puro para editar/deletar pelo ID
    rules_data = repo._load_rules_data()
    
    st.info("Estas sãos as regras de monitoramento que eu criei para você.")
    
    if not rules_data:
        st.write("*Nenhuma regra ativa no momento.*")
        return

    for i, rule in enumerate(rules_data):
        with st.container(border=True):
            cols = st.columns([0.8, 0.2])
            with cols[0]:
                tipo = rule.get('period', 'monthly')
                tipo_display = "MENSAL" if tipo == 'monthly' else "SEMANAL"
                tipo_icon = "📅" if tipo == 'monthly' else "📆"
                st.markdown(f"**{rule.get('category')}** > R$ {rule.get('threshold')}")
                st.caption(f"{tipo_icon} {tipo_display} | {rule.get('custom_message', 'Alerta Padrão')}")
            with cols[1]:
                if st.button("Remover", key=f"del_rule_{rule.get('id')}"):
                    repo.remove_rule(rule.get('id'))
                    st.success("Regra removida!")
                    st.rerun()

def main():
    render_profile_editor_api(api_client)

    # --- NOVO: Visualização da Inteligência ---
    render_mind_viewer(config_service)
    render_watchdog_viewer(config_service)
    
    # Serviços Locais para Administração
    # Nota: llm_orchestrator pode ser None se mudarmos o utils, mas aqui assumimos que existe
    # para passar ao OnboardingOrchestrator
    auth_service = GoogleAuthService(config_service)
    
    render_advanced_settings_local(config_service, auth_service, api_client)
    
    # OnboardingOrchestrator precisa de llm_orchestrator para reset? 
    # reset_config() usa config_service.
    # Mas o construtor pede llm.
    if "onboarding_orchestrator" not in st.session_state:
        # Se llm_orchestrator for None (fase futura), teremos problema aqui.
        # Por enquanto mantemos.
        st.session_state.onboarding_orchestrator = OnboardingOrchestrator(
            config_service, llm_orchestrator
        )
            
    render_danger_zone_local(st.session_state.onboarding_orchestrator)

if __name__ == "__main__":
    main()
