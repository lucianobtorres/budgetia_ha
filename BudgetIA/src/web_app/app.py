# src/web_app/app.py
import time
from pathlib import Path
from typing import Any

import streamlit as st

# Imports do seu projeto
from config import DATA_DIR
from core.agent_runner_interface import AgentRunner
from finance.planilha_manager import PlanilhaManager
from initialization.system_initializer import initialize_financial_system

# Importa o novo Manager
from web_app.onboarding_manager import OnboardingManager


# --- Função load_financial_system (permanece a mesma) ---
# @st.cache_resource
def load_financial_system(
    planilha_path: str,
) -> tuple[PlanilhaManager | None, Any | None, Any | None, bool]:
    # ... (Sua função de load_financial_system não muda) ...
    print(f"\n--- DEBUG: Entrando em load_financial_system para '{planilha_path}' ---")
    try:
        print("--- DEBUG: Chamando initialize_financial_system... ---")
        plan_manager, agent_runner, llm_orchestrator, dados_adicionados = (
            initialize_financial_system(planilha_path)
        )
        print("--- DEBUG: initialize_financial_system RETORNOU: ---")
        if plan_manager and agent_runner and llm_orchestrator:
            print("--- DEBUG: load_financial_system retornando objetos válidos. ---")
            return plan_manager, agent_runner, llm_orchestrator, dados_adicionados
        else:
            st.error("Falha interna ao inicializar componentes.")
            st.stop()
            return None, None, None, False
    except Exception as e:
        print(f"--- DEBUG ERROR: Exception em load_financial_system: {e} ---")
        st.error(f"Erro inesperado ao carregar sistema: {e}")
        st.stop()
        return None, None, None, False


# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="BudgetIA",
    page_icon="💰",
    layout="wide",
)

# --- INICIALIZAÇÃO DO ONBOARDING MANAGER ---
if "onboarding_manager" not in st.session_state:
    st.session_state.onboarding_manager = OnboardingManager()

manager: OnboardingManager = st.session_state.onboarding_manager

# --- LÓGICA DE INICIALIZAÇÃO REFINADA ---

# 1. FASE 1: SETUP DA PLANILHA
if not manager.is_planilha_setup_complete():
    print("--- DEBUG APP: FASE 1 (Planilha Setup) ---")
    st.title("💰 Bem-vindo ao BudgetIA!")
    st.info("Para começar, precisamos de uma planilha.")

    col1, col2 = st.columns(2)
    with col1:  # Criar Nova
        st.subheader("🚀 Criar Nova Planilha Mestra")
        default_path = str(Path(DATA_DIR) / "planilha_mestra.xlsx")
        novo_path_input = st.text_input("Nome e local:", default_path, key="novo_path")

        if st.button("Criar e Usar", key="criar_nova"):
            # Chama a lógica de negócios
            success, message = manager.create_new_planilha(
                novo_path_input, initialize_financial_system
            )
            if success:
                st.success(message)
                time.sleep(1)
                st.rerun()
            else:
                st.error(message)

    with col2:  # Usar Existente
        st.subheader("📂 Usar Minha Planilha Existente")
        uploaded_file = st.file_uploader(
            "Carregar (.xlsx)", type=["xlsx"], key="uploader"
        )
        if uploaded_file is not None:
            # Chama a lógica de negócios
            success, message = manager.handle_uploaded_planilha(
                uploaded_file, DATA_DIR, initialize_financial_system
            )
            if success:
                st.success(message)
                time.sleep(1)
                st.rerun()
            else:
                st.error(message)

        st.markdown("--- OU ---")
        path_input = st.text_input("Insira o caminho completo:", key="path_input")
        if st.button("Usar por Caminho", key="usar_path"):
            # Chama a lógica de negócios
            success, message = manager.set_planilha_from_path(
                path_input, initialize_financial_system
            )
            if success:
                st.success(message)
                time.sleep(1)
                st.rerun()
            else:
                st.error(message)

    st.stop()  # Para a execução até a Fase 1 ser concluída

# --- SE CHEGOU AQUI, FASE 1 ESTÁ COMPLETA ---
print("--- DEBUG APP: FASE 1 OK. Carregando sistema... ---")
current_planilha_path = manager.planilha_path

# 2. CARREGAMENTO DO SISTEMA
# (Só carrega se os objetos ainda não estiverem no cache/session_state)
if "plan_manager" not in st.session_state:
    print(f"--- DEBUG APP: Carregando sistema para: {current_planilha_path} ---")
    plan_manager, agent_runner, llm_orchestrator, dados_adicionados = (
        load_financial_system(current_planilha_path)
    )

    if plan_manager and agent_runner and llm_orchestrator:
        st.session_state.plan_manager = plan_manager
        st.session_state.agent_runner = agent_runner
        st.session_state.llm_orchestrator = llm_orchestrator
        st.session_state.current_planilha_path = current_planilha_path
        if dados_adicionados and "dados_exemplo_msg_mostrada" not in st.session_state:
            st.success("Dados de exemplo foram carregados na sua planilha!")
            st.session_state.dados_exemplo_msg_mostrada = True
    else:
        st.error("Falha crítica ao carregar componentes do sistema.")
        if st.button("Tentar Novamente (Limpar Configuração)"):
            manager.reset_config()
            st.rerun()
        st.stop()

# Recupera os objetos carregados
plan_manager: PlanilhaManager = st.session_state.plan_manager
agent_runner: AgentRunner = st.session_state.agent_runner

# 3. FASE 2: SETUP DO PERFIL
if not manager.verificar_perfil_preenchido(plan_manager):
    print("--- DEBUG APP: FASE 2 (Profile Setup) ---")
    st.header("✨ Configurando seu Perfil Financeiro")
    st.warning("Seu perfil financeiro parece incompleto...")
    st.markdown(
        "Converse com a IA abaixo para configurar sua **Renda Mensal Média** e **Principal Objetivo Financeiro**:"
    )

    if "onboarding_messages" not in st.session_state:
        st.session_state.onboarding_messages = [
            {
                "role": "assistant",
                "content": "Olá! Para começar, qual sua Renda Mensal Média?",
            }
        ]

    for message in st.session_state.onboarding_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Responda à IA...", key="onboarding_input"):
        st.session_state.onboarding_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analisando e salvando..."):
                # Chama a lógica de negócios
                output = manager.process_profile_input(prompt, agent_runner)

                st.markdown(output)
                st.session_state.onboarding_messages.append(
                    {"role": "assistant", "content": output}
                )

                # Verifica DEPOIS da IA rodar
                if manager.verificar_perfil_preenchido(plan_manager):
                    st.success("Perfil configurado! Redirecionando...")
                    time.sleep(2)
                    st.rerun()

    st.stop()  # Para a execução até a Fase 2 ser concluída

# --- SE CHEGOU AQUI, ONBOARDING COMPLETO ---
print("--- DEBUG APP: Onboarding completo. Renderizando páginas. ---")

st.caption(f"Arquivo da planilha: `{st.session_state.current_planilha_path}`")
# A partir daqui, o Streamlit assume e renderiza a página selecionada
# (ex: 1_📊_Dashboard.py)
