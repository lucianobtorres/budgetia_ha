# src/web_app/ui_components/ui_home_hub.py
import streamlit as st


def render() -> None:
    """Renderiza a home page principal (Hub de Navegação)."""
    st.title("💰 Bem-vindo ao BudgetIA!")
    st.subheader("O que você gostaria de fazer?")

    col1, col2 = st.columns(2)
    with col1:
        st.page_link(
            "pages/1_📊_Dashboard.py",
            label="**Ver meu Dashboard**",
            icon="📊",
            use_container_width=True,
        )
        st.page_link(
            "pages/2_💬_Chat_com_IA.py",
            label="**Conversar com a IA**",
            icon="💬",
            use_container_width=True,
        )
    with col2:
        st.page_link(
            "pages/4_🎯_Meus_Orcamentos.py",
            label="**Gerenciar Orçamentos**",
            icon="🎯",
            use_container_width=True,
        )
        st.page_link(
            "pages/3_📝_Editar_Transacoes.py",
            label="**Editar Transações**",
            icon="📝",
            use_container_width=True,
        )

    st.divider()
    st.page_link(
        "pages/5_👤_Perfil_Financeiro.py",
        label="Ajustar meu Perfil",
        icon="👤",
    )

    st.caption(f"Arquivo da planilha: `{st.session_state.current_planilha_path}`")
