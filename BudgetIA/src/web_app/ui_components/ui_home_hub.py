# Em: src/web_app/ui_components/ui_home_hub.py

import streamlit as st

import config

# --- NOVOS IMPORTS ---
from web_app.api_client import BudgetAPIClient
from app.chat_history_manager import StreamlitHistoryManager
# --- FIM NOVOS IMPORTS ---




print("--- RELOADED UI_HOME_HUB (V2) ---")

def _render_dashboard_metrics(api_client: BudgetAPIClient) -> None:
    """Renderiza os KPIs e gráficos do dashboard buscando da API."""
    # (Esta função não muda em nada)
    st.title("Meu Mentor Financeiro 💰")
    st.info(
        "Este é o seu Hub de IA. Visualize seus dados e converse com seu mentor abaixo."
    )
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
            # API retorna lista de dicts
            orcamentos_ativos = api_client.get_budgets_status()
            
            if orcamentos_ativos:
                for row in orcamentos_ativos:
                    categoria = row[config.ColunasOrcamentos.CATEGORIA]
                    gasto = row[config.ColunasOrcamentos.GASTO]
                    limite = row[config.ColunasOrcamentos.LIMITE]
                    percentual_real = (gasto / limite) * 100 if limite > 0 else 0

                    percentual_para_barra = min(percentual_real, 100)
                    label_texto = (
                        f"**{categoria}**: Gasto R$ {gasto:,.2f} de R$ {limite:,.2f}"
                    )

                    if percentual_real > 100:
                        label_texto += f" ⚠️ **({percentual_real:.0f}%)**"

                    st.markdown(label_texto)  # Usa o novo texto
                    st.progress(int(percentual_para_barra))
            else:
                st.info("Sem orçamentos mensais ativos.")
    else:
        st.info(
            "Seu dashboard está vazio. "
            "Adicione transações usando o chat abaixo para começar."
        )
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
            st.write(message["content"])  # Usando st.write como pedido

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

                # 2. Envia para a API
                response_text = api_client.send_chat_message(prompt)

                # 3. Adiciona resposta da IA ao histórico local
                if response_text:
                    history_manager.add_message("assistant", response_text)
                    st.write(response_text)
                else:
                    st.error("Erro ao comunicar com a IA.")

        # O Rerun vai recarregar a UI, e o loop lá em cima
        # vai ler o histórico atualizado (incluindo a resposta)
        st.rerun()


def render_sidebar_export() -> None:
    """Renderiza a funcionalidade 'Salvar Como' na barra lateral."""

    # plan_manager não é mais necessário aqui se usarmos a exportação da API
    # Mas como o código abaixo usa 'create_excel_export_bytes(plan_manager)',
    # vamos mudar para usar 'api_client.export_excel_bytes()'
    
    api_client: BudgetAPIClient = st.session_state.api_client

    with st.sidebar:
        st.subheader("Salvar Como")
        st.caption("Salve uma cópia local (em .xlsx) de todos os seus dados atuais.")

        # O nome do arquivo agora é usado pelos dois botões
        file_name = st.text_input(
            "Nome do arquivo:",
            value="budgetia_export.xlsx",
            help="O nome que o arquivo terá no seu computador.",
        )

        # --- LÓGICA DE PREPARAÇÃO E DOWNLOAD ---

        # 1. Botão de Preparar:
        # Este botão executa a função pesada e salva os bytes na sessão.
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
                        # O FEEDBACK QUE VOCÊ PEDIU!
                        st.toast("Arquivo pronto para baixar!", icon="✅")
                    else:
                        st.error("Falha ao gerar o arquivo.")

        # 2. Botão de Download:
        # Este botão SÓ aparece se os dados estiverem prontos na sessão.
        if "download_data" in st.session_state:
            download_info = st.session_state.download_data

            # Verifica se o usuário mudou o nome do arquivo APÓS preparar
            if file_name != download_info["file_name"]:
                st.warning(
                    "O nome do arquivo mudou. Clique em 'Preparar' novamente para atualizar."
                )
                # Limpa os dados antigos para evitar confusão
                del st.session_state.download_data
            else:
                # O botão de download real
                st.download_button(
                    label="Baixar",
                    data=download_info["bytes"],
                    file_name=download_info["file_name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary",
                    # Limpa o estado da sessão após o clique
                    on_click=lambda: st.session_state.pop("download_data"),
                )


def render(
    api_client: BudgetAPIClient
) -> None:
    """Renderiza o Hub de IA principal, combinando Dashboard e Chat."""
    """Renderiza o Hub de IA principal, combinando Dashboard e Chat."""

    # 1. Renderiza o Dashboard no topo
    with st.expander("Ver Dashboard e Métricas 📊", expanded=True):
        _render_dashboard_metrics(api_client)

    # 2. Renderiza a Interface de Chat abaixo
    _render_chat_interface(api_client)

    # 3. Renderiza a funcionalidade de exportação na sidebar
    render_sidebar_export()
