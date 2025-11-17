# Em: src/initialization/system_initializer.py
import os
import sys

from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider
from core.user_config_service import UserConfigService
from finance.storage.base_storage_handler import BaseStorageHandler
from finance.storage.google_drive_handler import GoogleDriveFileHandler
from finance.storage.google_sheets_storage_handler import GoogleSheetsStorageHandler

# Adiciona o 'src' ao path (seu arquivo já deve ter isso)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from agent_implementations.langchain_agent import IADeFinancas
from finance.planilha_manager import PlanilhaManager

# --- 1. IMPORTAR AMBOS OS HANDLERS E A INTERFACE ---
from finance.storage.excel_storage_handler import ExcelHandler


def _create_storage_handler(planilha_path: str) -> BaseStorageHandler:
    """Fábrica (Factory) para decidir qual Handler de armazenamento usar."""
    # (Esta função que criamos está correta e permanece a mesma)
    print(f"--- DEBUG INITIALIZER: Criando handler para: {planilha_path} ---")

    if "drive.google.com/file" in planilha_path:
        print(
            "--- DEBUG INITIALIZER: Detectado arquivo Excel no Google Drive (Link Direto). ---"
        )
        return GoogleDriveFileHandler(file_url=planilha_path)
    elif "docs.google.com/spreadsheets" in planilha_path and "sd=true" in planilha_path:
        print(
            "--- DEBUG INITIALIZER: Detectado arquivo Excel no Google Drive (Link de Visualização). ---"
        )
        return GoogleDriveFileHandler(file_url=planilha_path)
    elif "docs.google.com/spreadsheets" in planilha_path:
        print("--- DEBUG INITIALIZER: Detectado Google Sheets (Nativo). ---")
        return GoogleSheetsStorageHandler(spreadsheet_url_or_key=planilha_path)
    else:
        print("--- DEBUG INITIALIZER: Detectado arquivo Excel local. ---")
        return ExcelHandler(file_path=planilha_path)


def initialize_financial_system(
    planilha_path: str,
    llm_orchestrator: LLMOrchestrator,
    config_service: UserConfigService,
) -> tuple[PlanilhaManager | None, AgentRunner | None, LLMOrchestrator | None, bool]:
    """
    Inicializa e conecta todos os componentes do sistema financeiro.
    """
    print(f"\n--- DEBUG INITIALIZER: Iniciando para '{planilha_path}' ---")

    plan_manager: PlanilhaManager | None = None
    agent_runner: AgentRunner | None = None
    dados_de_exemplo_foram_adicionados = False

    try:
        storage_handler = _create_storage_handler(planilha_path)

        # --- 3. INJETAR O HANDLER ABSTRATO ---
        # (Nenhuma mudança daqui para baixo, já está correto)
        plan_manager = PlanilhaManager(
            storage_handler=storage_handler, config_service=config_service
        )
        print(
            f"--- DEBUG INITIALIZER: PlanilhaManager criado: {type(plan_manager)} ---"
        )

        is_new_file = plan_manager.is_new_file
        dados_de_exemplo_foram_adicionados = False

        if is_new_file:
            df_transacoes = plan_manager.visualizar_dados(config.NomesAbas.TRANSACOES)
            if not df_transacoes.empty:
                dados_de_exemplo_foram_adicionados = True
                print("--- DEBUG INITIALIZER: Dados de exemplo foram adicionados. ---")

        # --- 2. Inicialização da IA e do Agente ---
        print("--- DEBUG INITIALIZER: Configurando LLM e Agente... ---")
        primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
        llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
        llm_orchestrator.get_configured_llm()

        contexto_perfil = plan_manager.get_perfil_como_texto()
        print(
            f"--- DEBUG INITIALIZER: Contexto do Perfil injetado no Agente: {contexto_perfil[:50]}... ---"
        )

        agent_runner = IADeFinancas(
            llm_orchestrator=llm_orchestrator,
            contexto_perfil=contexto_perfil,
            data_context=plan_manager._context,
            transaction_repo=plan_manager.transaction_repo,
            budget_repo=plan_manager.budget_repo,
            debt_repo=plan_manager.debt_repo,
            profile_repo=plan_manager.profile_repo,
            insight_repo=plan_manager.insight_repo,
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

        traceback.print_exc()
        return None, None, None, False
