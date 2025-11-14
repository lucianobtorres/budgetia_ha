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
        mapeamento = config_service.get_mapeamento()

        # --- 2. LÓGICA DE ESCOLHA DO HANDLER ---
        storage_handler: BaseStorageHandler

        # 1. É um link de ARQUIVO do Drive (nativo .xlsx)?
        if "drive.google.com/file" in planilha_path:
            print(
                "--- DEBUG INITIALIZER: Detectado arquivo Excel no Google Drive (Link Direto). ---"
            )
            storage_handler = GoogleDriveFileHandler(file_url=planilha_path)

        # 2. É um link de Google Sheet que aponta para um Excel (modo de compatibilidade)?
        elif "docs.google.com/" in planilha_path and "sd=true" in planilha_path:
            print(
                "--- DEBUG INITIALIZER: Detectado arquivo Excel no Google Drive (Link de Visualização). ---"
            )
            storage_handler = GoogleDriveFileHandler(file_url=planilha_path)

        # 3. É um link de Google Sheet (nativo)?
        elif "docs.google.com/" in planilha_path:
            print("--- DEBUG INITIALIZER: Detectado Google Sheets (Nativo). ---")
            storage_handler = GoogleSheetsStorageHandler(
                spreadsheet_url_or_key=planilha_path
            )

        # 4. É um arquivo local?
        else:
            print("--- DEBUG INITIALIZER: Detectado arquivo Excel local. ---")
            storage_handler = ExcelHandler(file_path=planilha_path)
        # --- FIM DA LÓGICA DE ESCOLHA ---

        # --- 3. INJETAR O HANDLER ABSTRATO ---
        # (Nenhuma mudança daqui para baixo, já está correto)
        plan_manager = PlanilhaManager(
            storage_handler=storage_handler, mapeamento=mapeamento
        )
        print(
            f"--- DEBUG INITIALIZER: PlanilhaManager criado: {type(plan_manager)} ---"
        )

        is_new_file = plan_manager.is_new_file
        dados_de_exemplo_foram_adicionados = False
        if is_new_file and mapeamento is None:
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
