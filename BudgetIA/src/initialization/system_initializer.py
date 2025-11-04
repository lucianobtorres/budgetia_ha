# Em: src/initialization/system_initializer.py

import json
import os

# --- CORREÇÃO DE IMPORTS ---
# Adicionar o 'src' ao path para encontrar web_app.utils
import sys
from typing import Any  # Imports atualizados

import config

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from web_app.utils import PLANILHA_KEY, load_persistent_config
except ImportError as e:
    print(f"ERRO CRÍTICO: Não foi possível importar 'web_app.utils': {e}.")

    # Define funções dummy para evitar que o app quebre
    def load_persistent_config() -> dict:
        return {}

    PLANILHA_KEY = "planilha_path"
# --- FIM CORREÇÃO IMPORTS ---

from agent_implementations.langchain_agent import IADeFinancas
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider
from finance.excel_handler import ExcelHandler
from finance.planilha_manager import PlanilhaManager


def _carregar_dados_exemplo(file_path: str) -> list[dict[str, Any]]:
    # ... (Sua função _carregar_dados_exemplo permanece igual) ...
    try:
        with open(file_path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            transacoes: list[dict[str, Any]] = data.get("transacoes", [])
            return transacoes
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"ERRO: Arquivo de dados de exemplo não encontrado...: {file_path}")
        return []


# --- ASSINATURA DA FUNÇÃO MODIFICADA ---
def initialize_financial_system(
    planilha_path: str,
) -> tuple[PlanilhaManager | None, AgentRunner | None, LLMOrchestrator | None, bool]:
    """
    Inicializa e conecta todos os componentes do sistema financeiro.
    """
    print(f"\n--- DEBUG INITIALIZER: Iniciando para '{planilha_path}' ---")

    plan_manager = None  # Inicializa como None
    agent_runner = None
    llm_orchestrator = None
    dados_de_exemplo_foram_adicionados = False

    try:
        # --- ALTERAÇÃO 1: Carregar o config persistente e buscar o mapa ---
        config_persistente = load_persistent_config()
        mapeamento = config_persistente.get("mapeamento")  # Será None se não existir

        if mapeamento:
            print("--- DEBUG INITIALIZER: Mapeamento de usuário encontrado! ---")
        else:
            print(
                "--- DEBUG INITIALIZER: Nenhum mapeamento encontrado, usando layout padrão. ---"
            )

        excel_handler = ExcelHandler(file_path=planilha_path)

        # --- 1. Inicialização do Gerenciador da Planilha ---
        print("--- DEBUG INITIALIZER: Criando PlanilhaManager... ---")
        # --- ALTERAÇÃO 2: Passar o 'mapeamento' para o construtor ---
        plan_manager = PlanilhaManager(
            excel_handler=excel_handler,
            mapeamento=mapeamento,  # Passa o mapa (ou None)
        )
        print(
            f"--- DEBUG INITIALIZER: PlanilhaManager criado: {type(plan_manager)} ---"
        )

        # --- ALTERAÇÃO 3: Usar o atributo do plan_manager ---
        is_new_file = plan_manager.is_new_file

        # A lógica de popular dados já está no __init__ do PlanilhaManager
        # Precisamos apenas saber se foi populado para o app.py
        if is_new_file and mapeamento is None:
            if not plan_manager.visualizar_dados(config.NomesAbas.TRANSACOES).empty:
                dados_de_exemplo_foram_adicionados = True
                print("--- DEBUG INITIALIZER: Dados de exemplo foram adicionados. ---")

        # A lógica de recalcular já está no __init__ do PlanilhaManager se não for novo
        # (Não precisamos chamar de novo)

        # --- 4. Inicialização da IA e do Agente ---
        print("--- DEBUG INITIALIZER: Configurando LLM e Agente... ---")
        primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
        llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
        llm_orchestrator.get_configured_llm()

        # --- ALTERAÇÃO 4: Injetar contexto do perfil no Agente ---
        contexto_perfil = plan_manager.get_perfil_como_texto()
        print(
            f"--- DEBUG INITIALIZER: Contexto do Perfil injetado no Agente: {contexto_perfil[:50]}... ---"
        )

        agent_runner = IADeFinancas(
            planilha_manager=plan_manager,
            llm_orchestrator=llm_orchestrator,
            contexto_perfil=contexto_perfil,  # Passa o contexto para o Agente
        )

        print("--- DEBUG INITIALIZER: Inicialização BEM SUCEDIDA. ---")
        return (
            plan_manager,
            agent_runner,
            llm_orchestrator,
            dados_de_exemplo_foram_adicionados,
        )
    except Exception as e:
        print(f"--- DEBUG INITIALIZER ERROR: Erro durante a inicialização: {e} ---")
        import traceback

        traceback.print_exc()  # Imprime o traceback completo no terminal
        return None, None, None, False
