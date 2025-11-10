# Em: src/web_app/ui_components/ui_home_hub.py

import streamlit as st

import config
from core.agent_runner_interface import AgentRunner
from finance.planilha_manager import PlanilhaManager


def _render_dashboard_metrics(plan_manager: PlanilhaManager) -> None:
    """Renderiza os KPIs e gráficos do dashboard."""

    st.title("Meu Mentor Financeiro 💰")
    st.info(
        "Este é o seu Hub de IA. Visualize seus dados e converse com seu mentor abaixo."
    )

    summary = plan_manager.get_summary()

    if summary and (
        summary.get(config.SummaryKeys.RECEITAS, 0) > 0
        or summary.get(config.SummaryKeys.DESPESAS, 0) > 0
    ):
        # --- 1. KPIs (Métricas Principais) ---
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

        # --- 2. Gráficos (Lado a Lado, como você sugeriu) ---
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
            # Filtra orçamentos ativos para o hub
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

    # 3. Renderiza o Rodapé com a informação do arquivo
    if "current_planilha_path" in st.session_state:
        st.caption(
            f"Planilha ativa: {st.session_state.current_planilha_path}",
            help="Para alterar a planilha, use a 'Zona de Perigo' na página 'Perfil Financeiro'.",
        )


def _render_chat_interface(agent_runner: AgentRunner) -> None:
    """Renderiza a interface de chat (histórico e input)."""

    # Inicializa o histórico do chat na sessão se não existir
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Exibe o histórico de mensagens
    # Usamos .markdown() para corrigir o bug de formatação
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input do chat (ancorado no fundo da tela)
    if prompt := st.chat_input(
        "Fale com o BudgetIA... (ex: Adicione R$50 em Alimentação)"
    ):
        # Adiciona e exibe a mensagem do usuário
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Gera e exibe a resposta da IA
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                response = agent_runner.interagir(prompt)
                print(
                    f"--- DEBUG (Hub): Resposta da IA (bruta via repr): {repr(response)} ---"
                )

                # Usa .markdown() para formatar corretamente a saída
                st.write(response)

                st.session_state.chat_history.append(
                    {"role": "assistant", "content": response}
                )
        st.rerun()


def render() -> None:
    """Renderiza o Hub de IA principal, combinando Dashboard e Chat."""

    # Carrega os objetos principais da sessão
    if "plan_manager" not in st.session_state or "agent_runner" not in st.session_state:
        st.error("Erro: Sessão não inicializada corretamente.")
        st.warning("Por favor, recarregue a aplicação.")
        st.stop()

    plan_manager: PlanilhaManager = st.session_state.plan_manager
    agent_runner: AgentRunner = st.session_state.agent_runner

    # 1. Renderiza o Dashboard no topo
    with st.expander("Ver Dashboard e Métricas 📊", expanded=True):
        _render_dashboard_metrics(plan_manager)

    # 2. Renderiza a Interface de Chat abaixo
    _render_chat_interface(agent_runner)
