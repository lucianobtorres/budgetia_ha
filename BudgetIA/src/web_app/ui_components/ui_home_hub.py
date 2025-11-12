# Em: src/web_app/ui_components/ui_home_hub.py

import streamlit as st

import config

# --- NOVOS IMPORTS ---
from app.chat_service import ChatService

# Remover 'AgentRunner'
# --- FIM NOVOS IMPORTS ---
from finance.planilha_manager import PlanilhaManager


def _render_dashboard_metrics(plan_manager: PlanilhaManager) -> None:
    """Renderiza os KPIs e gráficos do dashboard."""
    # (Esta função não muda em nada)
    st.title("Meu Mentor Financeiro 💰")
    st.info(
        "Este é o seu Hub de IA. Visualize seus dados e converse com seu mentor abaixo."
    )
    summary = plan_manager.get_summary()
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
            despesas_por_categoria = plan_manager.get_expenses_by_category(top_n=5)
            if not despesas_por_categoria.empty:
                st.bar_chart(despesas_por_categoria)
            else:
                st.info("Sem despesas para exibir no gráfico.")
        with col_graf_2:
            st.subheader("Status dos Orçamentos")
            df_orcamentos = plan_manager.visualizar_dados(
                aba_nome=config.NomesAbas.ORCAMENTOS
            )
            orcamentos_ativos = df_orcamentos[
                (df_orcamentos[config.ColunasOrcamentos.PERIODO] == "Mensal")
                & (df_orcamentos[config.ColunasOrcamentos.LIMITE] > 0)
            ]
            if not orcamentos_ativos.empty:
                for index, row in orcamentos_ativos.iterrows():
                    categoria = row[config.ColunasOrcamentos.CATEGORIA]
                    gasto = row[config.ColunasOrcamentos.GASTO]
                    limite = row[config.ColunasOrcamentos.LIMITE]
                    percentual = (gasto / limite) * 100 if limite > 0 else 0
                    st.markdown(
                        f"**{categoria}**: Gasto R$ {gasto:,.2f} de R$ {limite:,.2f}"
                    )
                    st.progress(int(percentual))
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


def _render_chat_interface(chat_service: ChatService) -> None:  # Recebe o ChatService
    """Renderiza a interface de chat (histórico e input)."""

    # Exibe o histórico de mensagens (lido do service)
    for message in chat_service.get_history():
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
                # O Service cuida de tudo:
                # 1. Salva 'prompt' no histórico
                # 2. Chama 'agent_runner.interagir()'
                # 3. Salva 'response' no histórico
                response = chat_service.handle_message(prompt)

                # Não precisamos fazer mais nada aqui

        # O Rerun vai recarregar a UI, e o loop lá em cima
        # vai ler o histórico atualizado (incluindo a resposta)
        st.rerun()


def render(
    plan_manager: PlanilhaManager, chat_service: ChatService
) -> None:  # Assinatura mudou
    """Renderiza o Hub de IA principal, combinando Dashboard e Chat."""

    # 1. Renderiza o Dashboard no topo
    with st.expander("Ver Dashboard e Métricas 📊", expanded=True):
        _render_dashboard_metrics(plan_manager)

    # 2. Renderiza a Interface de Chat abaixo
    _render_chat_interface(chat_service)
