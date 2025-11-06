# src/web_app/app.py

import time
from pathlib import Path
from typing import Any

import streamlit as st

# Imports do seu projeto
import config
from config import DATA_DIR
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider
from finance.planilha_manager import PlanilhaManager
from initialization.system_initializer import initialize_financial_system
from web_app.onboarding_manager import OnboardingManager


# --- Função load_financial_system (MODIFICADA E CORRIGIDA) ---
@st.cache_resource
def load_financial_system(
    planilha_path: str,
    _llm_orchestrator: LLMOrchestrator,
) -> tuple[PlanilhaManager | None, Any | None, Any | None, bool]:
    """
    Carrega o sistema. Usa o _llm_orchestrator como parte da chave de cache.
    """
    print(f"\n--- DEBUG: Entrando em load_financial_system para '{planilha_path}' ---")
    try:
        print("--- DEBUG: Chamando initialize_financial_system... ---")
        plan_manager, agent_runner, llm_orchestrator, dados_adicionados = (
            initialize_financial_system(planilha_path, _llm_orchestrator)
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

# --- INICIALIZAÇÃO GLOBAL (NO TOPO) ---


@st.cache_resource
def get_llm_orchestrator() -> LLMOrchestrator:
    """Cria e cacheia o LLMOrchestrator."""
    print("--- DEBUG APP: Criando LLMOrchestrator (cache_resource)... ---")
    primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
    orchestrator = LLMOrchestrator(primary_provider=primary_provider)
    orchestrator.get_configured_llm()
    return orchestrator


llm_orchestrator = get_llm_orchestrator()

if "onboarding_manager" not in st.session_state:
    st.session_state.onboarding_manager = OnboardingManager(llm_orchestrator)

manager: OnboardingManager = st.session_state.onboarding_manager

# --- LÓGICA DE INICIALIZAÇÃO REFINADA ---

current_state = manager.get_current_state()
print(f"--- DEBUG APP: Estado atual do OnboardingManager: {current_state} ---")

# --- ROTEAMENTO DE ESTADO ---

if current_state == "AWAITING_FILE_SELECTION":
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
                novo_path_input,
                lambda path: initialize_financial_system(path, llm_orchestrator),
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
            # Chama a lógica de negócios (Plano A)
            success, message = manager.handle_uploaded_planilha(
                uploaded_file,
                DATA_DIR,
            )
            if success:
                st.success(message)
                time.sleep(1)
            else:
                st.error(message)
            st.rerun()  # Sempre regarrega para ir para o próximo estado

        st.markdown("--- OU ---")
        path_input = st.text_input("Insira o caminho completo:", key="path_input")
        if st.button("Usar por Caminho", key="usar_path"):
            # Chama a lógica de negócios (Plano A)
            success, message = manager.set_planilha_from_path(
                path_input,
            )
            if success:
                st.success(message)
                time.sleep(1)
            else:
                st.error(message)
            st.rerun()  # Sempre regarrega para ir para o próximo estado

    st.stop()

elif current_state == "GENERATING_STRATEGY":
    st.title("💰 BudgetIA Analisando...")
    st.subheader("Sua planilha é única. Estou aprendendo a lê-la.")
    with st.spinner(
        "A IA está gerando e testando o código de tradução... (Isso pode levar um minuto)"
    ):
        # Esta é uma tela de espera. O `OnboardingManager` está trabalhando.
        # O `st.rerun()` no `handle_uploaded_planilha` nos trouxe aqui.
        # O `_processar_planilha_customizada` (que é síncrono) vai rodar
        # e o próximo `st.rerun()` (no `handle_uploaded_planilha`) nos levará
        # ao estado 'SETUP_COMPLETE' ou 'STRATEGY_FAILED_FALLBACK'.
        # Para um spinner real, a geração teria que ser assíncrona.
        # Por agora, esta tela piscará rapidamente.
        st.write("Processando...")

elif current_state == "STRATEGY_FAILED_FALLBACK":
    st.title("😕 Desculpe, não consegui ler sua planilha")
    st.error(
        f"A IA tentou {manager.max_retries} vezes criar um código de tradução, mas falhou."
    )
    st.subheader("Você tem estas opções para continuar:")

    st.markdown("**Opção 1 (Recomendado): Importação Guiada (Plano B)**")
    st.write(
        "Nós criaremos uma `planilha_mestra.xlsx` nova para você e faremos uma importação guiada dos seus dados antigos."
    )
    if st.button("Iniciar Importação Guiada"):
        # TODO: Implementar manager.start_guided_import()
        st.info("Funcionalidade 'Importação Guiada' ainda em construção.")
        # manager.start_guided_import(manager.get_failed_path()) # Precisamos salvar o caminho que falhou
        # st.rerun()

    st.markdown("**Opção 2 (Avançado): Estratégia Manual (Plano C)**")
    with st.expander("Instruções para desenvolvedores"):
        st.markdown(
            "Você pode escrever seu próprio script de estratégia em Python."
            "1. Abra a pasta `src/finance/strategies/`."
            "2. Copie `default_strategy.py` para `minha_estrategia.py`."
            "3. Edite `minha_estrategia.py` (classe `CustomStrategy`) para ler/escrever sua planilha."
            "4. Edite `data/user_config.json` e adicione a seção:\n"
            "```json\n"
            "{\n"
            '  "planilha_path": "C:\\\\caminho\\\\para\\\\sua\\\\planilha.xlsx",\n'
            '  "mapeamento": {\n'
            '    "strategy_module": "minha_estrategia"\n'
            "  }\n"
            "}\n"
            "```"
        )
    if st.button("Já fiz isso, recarregar sistema."):
        manager.set_state(
            "AWAITING_FILE_SELECTION"
        )  # Volta ao início para reler o config
        st.rerun()

    st.stop()


elif current_state == "SETUP_COMPLETE":
    # ... (Seu código original para FASE 2 - PERFIL e RENDERIZAÇÃO DE PÁGINAS) ...
    print("--- DEBUG APP: FASE 1 OK. Carregando sistema... ---")
    current_planilha_path = manager.planilha_path
    if not current_planilha_path:
        st.error(
            "Erro crítico: Estado completo, mas caminho da planilha não encontrado."
        )
        manager.reset_config()
        st.rerun()
        st.stop()

    if "plan_manager" not in st.session_state:
        plan_manager, agent_runner, llm_orchestrator_loaded, dados_adicionados = (
            load_financial_system(current_planilha_path, llm_orchestrator)
        )
        if plan_manager and agent_runner and llm_orchestrator_loaded:
            st.session_state.plan_manager = plan_manager
            st.session_state.agent_runner = agent_runner
            st.session_state.llm_orchestrator = llm_orchestrator_loaded
            st.session_state.current_planilha_path = current_planilha_path
            if (
                dados_adicionados
                and "dados_exemplo_msg_mostrada" not in st.session_state
            ):
                st.success("Dados de exemplo foram carregados na sua planilha!")
                st.session_state.dados_exemplo_msg_mostrada = True
        else:
            st.error("Falha crítica ao carregar componentes do sistema.")
            if st.button("Tentar Novamente (Limpar Configuração)"):
                manager.reset_config()
                st.cache_resource.clear()
                st.rerun()
            st.stop()

    plan_manager: PlanilhaManager = st.session_state.plan_manager
    agent_runner: AgentRunner = st.session_state.agent_runner

    # --- FASE 2: SETUP DO PERFIL ---
    if not manager.verificar_perfil_preenchido(plan_manager):
        print("--- DEBUG APP: FASE 2 (Profile Setup) ---")
        st.header("✨ Configurando seu Perfil Financeiro")
        # ... (O restante do seu código da FASE 2 permanece idêntico) ...
        # ... (chat_input, process_profile_input, etc.) ...
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
            st.session_state.onboarding_messages.append(
                {"role": "user", "content": prompt}
            )
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Analisando e salvando..."):
                    output = manager.process_profile_input(prompt, agent_runner)
                    st.markdown(output)
                    st.session_state.onboarding_messages.append(
                        {"role": "assistant", "content": output}
                    )
                    if manager.verificar_perfil_preenchido(plan_manager):
                        st.success("Perfil configurado! Redirecionando...")
                        time.sleep(2)
                        st.rerun()
        st.stop()

    # --- ONBOARDING COMPLETO ---
    print("--- DEBUG APP: Onboarding completo. Renderizando páginas. ---")
    st.caption(f"Arquivo da planilha: `{st.session_state.current_planilha_path}`")
