# Em: src/web_app/pages/5_👤_Perfil_Financeiro.py

import time

import pandas as pd
import streamlit as st

import config
from config import NomesAbas
from core.google_auth_service import GoogleAuthService
from web_app.onboarding_manager import OnboardingManager
from web_app.utils import (
    create_excel_export_bytes,
    initialize_session_auth,
    verificar_perfil_preenchido,
)

try:
    from ..ui_components.common_ui import setup_page
except ImportError:
    from web_app.ui_components.common_ui import setup_page

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

manager: OnboardingManager = st.session_state.onboarding_manager
aba_perfil = NomesAbas.PERFIL_FINANCEIRO
auth_service = GoogleAuthService(config_service)

st.header("Seus Dados de Perfil", divider="blue")

try:
    df_perfil = plan_manager.visualizar_dados(aba_nome=aba_perfil)
    st.info("Aqui estão os dados do seu perfil. O Chat com IA usa essas informações.")

    # Adiciona linhas padrão se estiver vazio ou faltando
    campos_essenciais = ["Renda Mensal Média", "Principal Objetivo"]
    campos_desejados = campos_essenciais + [
        "Tolerância a Risco"
    ]  # Adiciona outros que queremos

    dados_para_adicionar = []
    # Garante que a coluna 'Campo' exista antes de tentar acessá-la
    campos_existentes = (
        set(df_perfil["Campo"])
        if not df_perfil.empty and "Campo" in df_perfil.columns
        else set()
    )

    for campo in campos_desejados:
        if campo not in campos_existentes:
            dados_para_adicionar.append(
                {"Campo": campo, "Valor": None, "Observações": ""}
            )

    # Concatena os campos faltantes (se houver)
    if dados_para_adicionar:
        # Garante que o df_perfil tenha as colunas corretas antes de concatenar
        if df_perfil.empty:
            df_perfil = pd.DataFrame(columns=config.LAYOUT_PLANILHA[aba_perfil])

        df_perfil = pd.concat(
            [
                df_perfil,
                pd.DataFrame(
                    dados_para_adicionar, columns=config.LAYOUT_PLANILHA[aba_perfil]
                ),
            ],
            ignore_index=True,
        )
    if "Campo" in df_perfil.columns:
        df_perfil["Campo"] = df_perfil["Campo"].astype(str).fillna("")

    if "Valor" in df_perfil.columns:
        # A coluna 'Valor' também é TextColumn, pois armazena números (Renda)
        # e texto (Objetivo). Deve ser string.
        df_perfil["Valor"] = df_perfil["Valor"].astype(str).fillna("")

    if "Observações" in df_perfil.columns:
        df_perfil["Observações"] = df_perfil["Observações"].astype(str).fillna("")
    editor_key_perfil = "editor_perfil"

    edited_df_perfil = st.data_editor(
        df_perfil,
        num_rows="dynamic",  # Permite adicionar novos campos
        use_container_width=True,
        column_config={
            "Campo": st.column_config.TextColumn(
                required=True, help="Nome do dado (Ex: Renda Mensal Média)."
            ),
            "Valor": st.column_config.TextColumn(
                required=True, help="O valor correspondente ao campo."
            ),
            "Observações": st.column_config.TextColumn(help="Notas opcionais."),
        },
        hide_index=True,
        key=editor_key_perfil,
    )

    # Lógica de salvamento
    if not df_perfil.equals(edited_df_perfil):
        if st.button("Salvar Alterações no Perfil"):
            st.info("Salvando perfil...")
            try:
                # Remover linhas onde o Campo é vazio/nulo
                edited_df_perfil_cleaned = edited_df_perfil.dropna(subset=["Campo"])

                plan_manager.update_dataframe(aba_perfil, edited_df_perfil_cleaned)
                plan_manager.save()
                st.success("Perfil Financeiro atualizado com sucesso!")

                # Re-verifica o perfil para dar feedback imediato
                if verificar_perfil_preenchido(plan_manager):
                    st.info("Status: Perfil parece completo.")
                else:
                    st.warning(
                        "Status: Perfil ainda parece incompleto (campos essenciais podem estar vazios ou faltando)."
                    )

                st.rerun()  # Recarrega a página
            except Exception as e:
                st.error(f"Erro ao salvar alterações no Perfil: {e}")
                st.exception(e)
        else:
            st.warning("Você tem alterações não salvas.")

except Exception as e:
    st.error(f"Erro ao carregar o Perfil Financeiro: {e}")
    st.exception(e)


st.divider()
st.header("Configurações Avançadas", divider="blue")
planilha_path = config_service.get_planilha_path()

is_google_sheet = planilha_path and "docs.google.com" in planilha_path

with st.container(border=True):
    st.subheader("Conexões de Dados")
    st.info(f"**Planilha Ativa:** `{planilha_path}`")

    # --- Revogação Nível 1 (Backend Consent) ---
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
            disabled=(
                not auth_service.get_user_credentials()
            ),  # Desabilita se o Google não estiver logado
        )

        if novo_consentimento != consent_dado:
            file_id = auth_service._extract_file_id_from_url(planilha_path)

            if not file_id:
                st.error(
                    "Não foi possível extrair o ID do arquivo Google da sua planilha ativa."
                )

            # SE O USUÁRIO ESTÁ LIGANDO (Opt-in)
            elif novo_consentimento is True:
                with st.spinner("Compartilhando com o assistente..."):
                    success, msg = auth_service.share_file_with_service_account(file_id)
                    if success:
                        config_service.save_backend_consent(True)
                        st.success(f"Modo Proativo Habilitado! {msg}")
                        st.rerun()
                    else:
                        st.error(f"Falha ao habilitar: {msg}")

            # SE O USUÁRIO ESTÁ DESLIGANDO (Opt-out)
            elif novo_consentimento is False:
                with st.spinner("Revogando o acesso do assistente..."):
                    success, msg = (
                        auth_service.revoke_file_sharing_from_service_account(file_id)
                    )
                    if success:
                        config_service.save_backend_consent(False)
                        st.success(f"Modo Proativo Desabilitado! {msg}")
                        st.rerun()
                    else:
                        st.error(f"Falha ao desabilitar: {msg}")

    # --- Revogação Nível 2 (OAuth Consent) ---
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

# --- NOVA SEÇÃO: ZONA DE PERIGO ---
st.divider()
st.subheader("Configurações Avançadas")

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
    )

    if st.button(
        "Resetar e Configurar Nova Planilha",
        type="primary",
        use_container_width=True,
        key="reset_onboarding",
    ):
        # 1. Chama o reset do OnboardingManager
        # (Isso apaga o user_config.json)
        manager.reset_config()

        # 2. Limpa todos os objetos cacheados do Streamlit
        # (Isso força o load_financial_system e get_llm_orchestrator a recarregarem)
        st.cache_resource.clear()

        # 3. Limpa o session_state (opcional, mas recomendado)
        # (Isso remove plan_manager, agent_runner, etc.)
        for key in st.session_state.keys():
            if key not in ["authentication_status", "name", "username"]:
                del st.session_state[key]

        st.success("Configuração reiniciada! O BudgetIA pedirá uma nova planilha.")
        st.balloons()
        time.sleep(2)

        # 4. Navega de volta para a Home (que agora é o 🏠_Home.py)
        st.switch_page("💰_BudgetIA.py")  # (Ajuste se você usou outro nome)
