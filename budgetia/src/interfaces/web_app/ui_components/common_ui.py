# src/web_app/ui_components/common_ui.py
from typing import Any

import streamlit as st

try:
    from core.agent_runner_interface import AgentRunner
    from finance.planilha_manager import PlanilhaManager
except ImportError:
    PlanilhaManager = Any
    AgentRunner = Any


def setup_page(
    title: str, icon: str, subtitle: str | None = None
) -> tuple[PlanilhaManager, AgentRunner]:
    """
    Configura o cabeçalho padrão da página, o botão "Voltar" e
    valida o session_state (o "disclaimer").

    Retorna (plan_manager, agent_runner) se o sistema estiver carregado.
    Chama st.stop() se o sistema não estiver carregado.
    """

    # 1. Botão Voltar para Home
    # (Ajuste o nome do arquivo .py se for diferente)
    st.page_link("💰_BudgetIA.py", label="Voltar para a Home", icon="🏠")
    st.divider()

    # 2. Título e Subtítulo (passados como argumentos)
    st.title(f"{icon} {title}")
    if subtitle:
        st.subheader(subtitle)

    # 3. Verificação de Sessão (O "Disclaimer" que você mencionou)
    if "plan_manager" not in st.session_state or "agent_runner" not in st.session_state:
        st.error(
            "Erro: O sistema financeiro não foi carregado corretamente. "
            "Por favor, volte à página principal (💰_BudgetIA)."
        )
        st.stop()  # Para a execução da página aqui

        # A linha abaixo é para o type checker,
        # já que st.stop() levanta uma exceção
        return None, None

    # 4. Retorna os objetos
    plan_manager: PlanilhaManager = st.session_state.plan_manager
    agent_runner: AgentRunner = st.session_state.agent_runner

    return (plan_manager, agent_runner)
