# Em: src/web_app/pages/3_👤_Perfil_Financeiro.py

import time
from typing import TYPE_CHECKING

import streamlit as st

from config import PROFILE_DESIRED_FIELDS, ColunasPerfil, NomesAbas
from core.google_auth_service import GoogleAuthService
from initialization.onboarding.orchestrator import OnboardingOrchestrator
from web_app.utils import (
    create_excel_export_bytes,
    initialize_session_auth,
    verificar_perfil_preenchido,
)

if TYPE_CHECKING:
    from core.user_config_service import UserConfigService
    from finance.planilha_manager import PlanilhaManager

try:
    from ..ui_components.common_ui import setup_page
except ImportError:
    from web_app.ui_components.common_ui import setup_page


def render_profile_editor(plan_manager: "PlanilhaManager", aba_perfil: str) -> None:
    st.header("Seus Dados de Perfil", divider="blue")
    try:
        # Ensure desired fields exist
        plan_manager.ensure_profile_fields(PROFILE_DESIRED_FIELDS)
        df_perfil = plan_manager.visualizar_dados(aba_nome=aba_perfil)
        st.info(
            "Aqui estão os dados do seu perfil. O Chat com IA usa essas informações."
        )
        # Clean up for editor
        if ColunasPerfil.CAMPO in df_perfil.columns:
            df_perfil[ColunasPerfil.CAMPO] = (
                df_perfil[ColunasPerfil.CAMPO].astype(str).fillna("")
            )
        if ColunasPerfil.VALOR in df_perfil.columns:
            df_perfil[ColunasPerfil.VALOR] = (
                df_perfil[ColunasPerfil.VALOR].astype(str).fillna("")
            )
        if ColunasPerfil.OBS in df_perfil.columns:
            df_perfil[ColunasPerfil.OBS] = (
                df_perfil[ColunasPerfil.OBS].astype(str).fillna("")
            )
        editor_key_perfil = "editor_perfil"
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
                st.info("Salvando perfil...")
                try:
                    edited_df_perfil_cleaned = edited_df_perfil.dropna(
                        subset=[ColunasPerfil.CAMPO]
                    )
                    plan_manager.update_dataframe(aba_perfil, edited_df_perfil_cleaned)
                    plan_manager.save()
                    st.success("Perfil Financeiro atualizado com sucesso!")
                    if verificar_perfil_preenchido(plan_manager):
                        st.info("Status: Perfil parece completo.")
                    else:
                        st.warning(
                            "Status: Perfil ainda parece incompleto (campos essenciais podem estar vazios ou faltando)."
                        )
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar alterações no Perfil: {e}")
                    st.exception(e)
            else:
                st.warning("Você tem alterações não salvas.")
    except Exception as e:
        st.error(f"Erro ao carregar o Perfil Financeiro: {e}")
        st.exception(e)


def render_advanced_settings(
    config_service: "UserConfigService",
    auth_service: GoogleAuthService,
    plan_manager: "PlanilhaManager",
) -> None:
    st.divider()
    st.header("Configurações Avançadas", divider="blue")
    planilha_path = config_service.get_planilha_path()
    is_google_sheet = planilha_path and "docs.google.com" in planilha_path
    with st.container(border=True):
        st.subheader("Conexões de Dados")
        st.info(f"**Planilha Ativa:** `{planilha_path}`")
        if is_google_sheet:
            st.markdown("**Modo Proativo (Bot & Scheduler)**")
            consent_dado = config_service.get_backend_consent()
            help_text = "Permite que o BudgetIA (via Bot/Scheduler) leia e escreva na sua planilha 24/7, mesmo offline."
            if not auth_service.get_user_credentials():
                help_text = "Você precisa se conectar ao Google (na tela de seleção de arquivo) para gerenciar isso."
            novo_consentimento = st.toggle(
                "Habilitar recursos de back-end",
                value=consent_dado,
                help=help_text,
                disabled=(not auth_service.get_user_credentials()),
            )
            if novo_consentimento != consent_dado:
                file_id = auth_service._extract_file_id_from_url(planilha_path)
                if not file_id:
                    st.error(
                        "Não foi possível extrair o ID do arquivo Google da sua planilha ativa."
                    )
                elif novo_consentimento is True:
                    with st.spinner("Compartilhando com o assistente..."):
                        success, msg = auth_service.share_file_with_service_account(
                            file_id
                        )
                        if success:
                            config_service.save_backend_consent(True)
                            st.success(f"Modo Proativo Habilitado! {msg}")
                            st.rerun()
                        else:
                            st.error(f"Falha ao habilitar: {msg}")
                elif novo_consentimento is False:
                    with st.spinner("Revogando o acesso do assistente..."):
                        success, msg = (
                            auth_service.revoke_file_sharing_from_service_account(
                                file_id
                            )
                        )
                        if success:
                            config_service.save_backend_consent(False)
                            st.success(f"Modo Proativo Desabilitado! {msg}")
                            st.rerun()
                        else:
                            st.error(f"Falha ao desabilitar: {msg}")
        st.markdown("**Conexão com a Conta Google**")
        if auth_service.get_user_credentials():
            st.success("Você conectou sua conta Google.")
            if st.button(
                "Desconectar do Google",
                help="Revoga o acesso do BudgetIA à sua conta Google.",
            ):
                with st.spinner("Revogando token..."):
                    auth_service.revoke_google_oauth_token()
                    st.success(
                        "Conta Google desconectada. Você precisará logar novamente para usar o seletor de arquivos."
                    )
                    st.rerun()
        else:
            st.info(
                "Você não conectou sua conta Google. Use o botão 'Fazer login com o Google' na tela de seleção de arquivo."
            )
    with st.container(border=True):
        st.subheader("Sincronização de Cache")
        st.caption(
            "Se você editou sua planilha por fora do app (direto no Google Sheets) e o Bot está com dados antigos, use este botão."
        )
        if st.button(
            "Forçar Sincronização",
            help="Limpa o cache do Redis e força a releitura do arquivo Google.",
        ):
            with st.spinner("Limpando cache e recarregando dados da nuvem..."):
                plan_manager.clear_cache()
            st.success(
                "Sincronização concluída! O app e o bot agora têm os dados mais recentes."
            )
        excel_bytes = create_excel_export_bytes(plan_manager)
        st.download_button(
            label="Baixar Cópia Local (Salvar Como...)",
            data=excel_bytes,
            file_name="budgetia_backup.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_backup_advanced",
        )


def render_danger_zone(
    orchestrator: OnboardingOrchestrator, plan_manager: "PlanilhaManager"
) -> None:
    st.divider()
    st.subheader("Zona de Perigo")
    with st.expander("Zona de Perigo"):
        st.warning(
            "Atenção: A ação abaixo irá desconfigurar sua planilha atual e reiniciar o BudgetIA, pedindo uma nova planilha na próxima vez que você abrir o app."
        )
        excel_bytes = create_excel_export_bytes(plan_manager)
        st.download_button(
            label="Baixar Cópia Local (Salvar Como...)",
            data=excel_bytes,
            file_name="budgetia_backup.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_backup_danger",
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
            st.success("Configuração reiniciada! O BudgetIA pedirá uma nova planilha.")
            st.balloons()
            time.sleep(2)
            st.switch_page("💰_BudgetIA.py")


def main() -> None:
    is_logged_in, username, config_service, llm_orchestrator = initialize_session_auth()
    if not is_logged_in or not config_service or "plan_manager" not in st.session_state:
        st.warning(
            "Você precisa estar logado e ter uma planilha configurada para acessar esta página."
        )
        st.stop()
    plan_manager, agent_runner = setup_page(
        title="Perfil Financeiro",
        icon="👤",
        subtitle="Defina seus orçamentos por categoria ",
    )
    orchestrator: OnboardingOrchestrator = st.session_state.onboarding_orchestrator
    aba_perfil = NomesAbas.PERFIL_FINANCEIRO
    auth_service = GoogleAuthService(config_service)
    render_profile_editor(plan_manager, aba_perfil)
    render_advanced_settings(config_service, auth_service, plan_manager)
    render_danger_zone(orchestrator, plan_manager)


if __name__ == "__main__":
    main()
