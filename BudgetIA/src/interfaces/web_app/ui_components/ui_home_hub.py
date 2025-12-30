# Em: src/web_app/ui_components/ui_home_hub.py

import streamlit as st
import config
from core.exceptions import BudgetException, APIConnectionError
from core.logger import get_logger

logger = get_logger("UI_HomeHub")

# --- NOVOS IMPORTS ---
from interfaces.web_app.api_client import BudgetAPIClient
from application.chat_history_manager import StreamlitHistoryManager
# --- FIM NOVOS IMPORTS ---

logger.info("RELOADED UI_HOME_HUB (V2)")

def _render_dashboard_metrics(api_client: BudgetAPIClient) -> None:
    """Renderiza os KPIs e gráficos do dashboard buscando da API."""
    st.title("Meu Mentor Financeiro 💰")
    st.info(
        "Este é o seu Hub de IA. Visualize seus dados e converse com seu mentor abaixo."
    )

    try:
        summary = api_client.get_summary()
        
        if summary and (
            summary.get(config.SummaryKeys.RECEITAS, 0) > 0
            or summary.get(config.SummaryKeys.DESPESAS, 0) > 0
        ):
            col1, col2, col3 = st.columns(3)
            col1.metric(
                label="Total de Receitas",
                value=f"R$ {summary.get(config.SummaryKeys.RECEITAS, 0):,.2f}",
            )
            col2.metric(
                label="Total de Despesas",
                value=f"R$ {summary.get(config.SummaryKeys.DESPESAS, 0):,.2f}",
            )
            col3.metric(
                label="Saldo Atual",
                value=f"R$ {summary.get(config.SummaryKeys.SALDO, 0):,.2f}",
            )
            st.divider()
            col_graf_1, col_graf_2 = st.columns(2)
            with col_graf_1:
                st.subheader("Top 5 Despesas")
                despesas_por_categoria = api_client.get_expenses_chart_data(top_n=5)
                if despesas_por_categoria:
                    st.bar_chart(despesas_por_categoria)
                else:
                    st.info("Sem despesas para exibir no gráfico.")
            with col_graf_2:
                st.subheader("Status dos Orçamentos")
                orcamentos_ativos = api_client.get_budgets_status()
                
                if orcamentos_ativos:
                    for row in orcamentos_ativos:
                        categoria = row[config.ColunasOrcamentos.CATEGORIA]
                        gasto = row[config.ColunasOrcamentos.GASTO]
                        # Garante float
                        limite = float(row[config.ColunasOrcamentos.LIMITE] or 0)
                        percentual_real = (gasto / limite) * 100 if limite > 0 else 0

                        percentual_para_barra = min(percentual_real, 100)
                        label_texto = (
                            f"**{categoria}**: Gasto R$ {gasto:,.2f} de R$ {limite:,.2f}"
                        )

                        if percentual_real > 100:
                            label_texto += f" ⚠️ **({percentual_real:.0f}%)**"

                        st.markdown(label_texto)
                        st.progress(int(percentual_para_barra))
                else:
                    st.info("Sem orçamentos mensais ativos.")
        else:
            st.info(
                "Seu dashboard está vazio. "
                "Adicione transações usando o chat abaixo para começar."
            )
    except APIConnectionError:
        st.error("🔌 Falha de conexão com a API. Dados do dashboard indisponíveis.")
    except BudgetException as e:
        st.error(f"Erro ao carregar dashboard: {e}")
    
    st.divider()
    if "current_planilha_path" in st.session_state:
        st.caption(
            f"Planilha ativa: {st.session_state.current_planilha_path}",
            help="Para alterar a planilha, use a 'Zona de Perigo' na página 'Perfil Financeiro'.",
        )


def _render_chat_interface(api_client: BudgetAPIClient) -> None:
    """Renderiza a interface de chat (histórico e input)."""
    
    # Gerenciador de Histórico Local (apenas visualização)
    history_manager = StreamlitHistoryManager("chat_history")

    # Exibe o histórico de mensagens
    for message in history_manager.get_history():
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Input do chat (ancorado no fundo da tela)
    if prompt := st.chat_input(
        "Fale com o BudgetIA... (ex: Adicione R$50 em Alimentação)"
    ):
        # Exibe o prompt do usuário imediatamente (para UX)
        with st.chat_message("user"):
            st.write(prompt)

        # Processa a mensagem
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                # 1. Adiciona mensagem do usuário ao histórico local
                history_manager.add_message("user", prompt)

                # 2. Envia para a API com Error Handling
                response_text = "Desculpe, tive um problema."
                try:
                    response_text = api_client.send_chat_message(prompt)
                except APIConnectionError:
                    response_text = "🔌 Estou offline no momento. Verifique sua conexão com o servidor."
                except Exception as e:
                    response_text = f"❌ Ocorreu um erro: {e}"

                # 3. Adiciona resposta da IA ao histórico local
                history_manager.add_message("assistant", response_text)
                st.write(response_text)

        # O Rerun vai recarregar a UI
        st.rerun()


def render_sidebar_export() -> None:
    """Renderiza a funcionalidade 'Salvar Como' na barra lateral."""
    
    api_client: BudgetAPIClient = st.session_state.api_client

    with st.sidebar:
        st.subheader("Salvar Como")
        st.caption("Salve uma cópia local (em .xlsx) de todos os seus dados atuais.")

        file_name = st.text_input(
            "Nome do arquivo:",
            value="budgetia_export.xlsx",
            help="O nome que o arquivo terá no seu computador.",
        )

        # --- LÓGICA DE PREPARAÇÃO E DOWNLOAD ---

        if st.button(
            "Exportar",
            use_container_width=True,
            key="prep_download",
        ):
            if not file_name:
                st.warning("Por favor, insira um nome de arquivo.")
            else:
                with st.spinner("Gerando seu arquivo Excel..."):
                    excel_bytes, filename_api = api_client.export_excel_bytes()
                    if excel_bytes:
                        # Armazena os bytes e o nome do arquivo na sessão
                        st.session_state.download_data = {
                            "bytes": excel_bytes,
                            "file_name": file_name,
                        }
                        st.toast("Arquivo pronto para baixar!", icon="✅")
                    else:
                        st.error("Falha ao gerar o arquivo.")

        if "download_data" in st.session_state:
            download_info = st.session_state.download_data

            if file_name != download_info["file_name"]:
                st.warning(
                    "O nome do arquivo mudou. Clique em 'Preparar' novamente para atualizar."
                )
                del st.session_state.download_data
            else:
                st.download_button(
                    label="Baixar",
                    data=download_info["bytes"],
                    file_name=download_info["file_name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary",
                    on_click=lambda: st.session_state.pop("download_data"),
                )


def render(
    api_client: BudgetAPIClient
) -> None:
    """Renderiza o Hub de IA principal, combinando Dashboard e Chat."""

    # 1. Renderiza o Dashboard no topo
    with st.expander("Ver Dashboard e Métricas 📊", expanded=True):
        _render_dashboard_metrics(api_client)

    # 2. Renderiza a Interface de Chat abaixo
    _render_chat_interface(api_client)

    # 3. Renderiza a funcionalidade de exportação na sidebar
    render_sidebar_export()
