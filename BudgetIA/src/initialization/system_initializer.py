# Em: src/initialization/system_initializer.py

import json
import os
import sys
from typing import Any

import config

# Adicionar o 'src' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from web_app.utils import PLANILHA_KEY, load_persistent_config
except ImportError:
    print("AVISO: web_app.utils não encontrado (normal em alguns testes).")

    def load_persistent_config() -> dict:
        return {}

    PLANILHA_KEY = "planilha_path"

# Imports de componentes do sistema
from agent_implementations.langchain_agent import IADeFinancas
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator  # Importar o Type Hint
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
    llm_orchestrator: LLMOrchestrator,  # <-- NOVO ARGUMENTO RECEBIDO
) -> tuple[PlanilhaManager | None, AgentRunner | None, LLMOrchestrator | None, bool]:
    """
    Inicializa e conecta todos os componentes do sistema financeiro.
    """
    print(f"\n--- DEBUG INITIALIZER: Iniciando para '{planilha_path}' ---")

    plan_manager = None
    agent_runner = None
    dados_de_exemplo_foram_adicionados = False

    try:
        # --- LÓGICA DE MAPEAMENTO (permanece igual) ---
        config_persistente = load_persistent_config()
        mapeamento = config_persistente.get("mapeamento")
        if mapeamento:
            print("--- DEBUG INITIALIZER: Mapeamento de usuário encontrado! ---")
        else:
            print(
                "--- DEBUG INITIALIZER: Nenhum mapeamento encontrado, usando layout padrão. ---"
            )

        excel_handler = ExcelHandler(file_path=planilha_path)

        # --- 1. Inicialização do Gerenciador da Planilha ---
        print("--- DEBUG INITIALIZER: Criando PlanilhaManager... ---")
        plan_manager = PlanilhaManager(
            excel_handler=excel_handler,
            mapeamento=mapeamento,
        )
        print(
            f"--- DEBUG INITIALIZER: PlanilhaManager criado: {type(plan_manager)} ---"
        )
        is_new_file = plan_manager.is_new_file

        if is_new_file and mapeamento is None:
            if not plan_manager.visualizar_dados(config.NomesAbas.TRANSACOES).empty:
                dados_de_exemplo_foram_adicionados = True
                print("--- DEBUG INITIALIZER: Dados de exemplo foram adicionados. ---")

        # --- 4. Inicialização da IA e do Agente ---
        print(
            "--- DEBUG INITIALIZER: Configurando Agente (LLM já foi fornecido)... ---"
        )

        # (A criação do LLMOrchestrator foi removida daqui)

        contexto_perfil = plan_manager.get_perfil_como_texto()
        print(
            f"--- DEBUG INITIALIZER: Contexto do Perfil injetado no Agente: {contexto_perfil[:50]}... ---"
        )

        agent_runner = IADeFinancas(
            planilha_manager=plan_manager,
            llm_orchestrator=llm_orchestrator,  # <-- Usa o orquestrador recebido
            contexto_perfil=contexto_perfil,
        )

        print("--- DEBUG INITIALIZER: Inicialização BEM SUCEDIDA. ---")
        return (
            plan_manager,
            agent_runner,
            llm_orchestrator,  # Retorna o mesmo orquestrador
            dados_de_exemplo_foram_adicionados,
        )
    except Exception as e:
        print(f"--- DEBUG INITIALIZER ERROR: Erro durante a inicialização: {e} ---")
        import traceback

        traceback.print_exc()
        return None, None, None, False
