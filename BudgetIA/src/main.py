import os

import pandas as pd

from agent_implementations.factory import AgentFactory
from config import DEFAULT_GEMINI_MODEL, NomesAbas
from core.llm_enums import LLMProviderType
from core.llm_factory import LLMProviderFactory
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from finance.factory import FinancialSystemFactory
from finance.storage.excel_storage_handler import ExcelHandler


# Esta função ainda é útil para quando a IA precisar VER os dados
def formatar_dados_planilha_para_ia(df: pd.DataFrame) -> str:
    """
    Formata o DataFrame da planilha em um texto compreensível para a IA.
    Para uma análise inicial, podemos converter o DF em um JSON ou texto tabular.
    """
    if df.empty:
        return "Nenhum dado financeiro disponível na planilha para análise."
    return str(df.to_json(orient="records", indent=2, date_format="iso"))


def main() -> None:
    """
    Função principal que orquestra a leitura da planilha e a geração de insights pela IA.
    """
    print("Iniciando o Sistema de Gestão Financeira Inteligente...")

    # Definindo o caminho da planilha de forma robusta
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    planilha_path = os.path.join(project_root, "planilha_mestra.xlsx")

    # 1. Setup de Configuração e Storage
    config_service = UserConfigService("cli_user")  # Usuário padrão para CLI
    storage_handler = ExcelHandler(file_path=planilha_path)

    # 2. Inicializa o gerenciador da planilha via Factory
    plan_manager = FinancialSystemFactory.create_manager(
        storage_handler=storage_handler, config_service=config_service
    )

    # 3. Inicializa a IA
    primary_provider = LLMProviderFactory.create_provider(
        LLMProviderType.GEMINI, default_model=DEFAULT_GEMINI_MODEL
    )
    llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
    llm_orchestrator.get_configured_llm()

    ia_financas = AgentFactory.create_agent(
        llm_orchestrator=llm_orchestrator, plan_manager=plan_manager
    )

    print("\n--- Conversando com a IA (digite 'sair' para encerrar) ---")
    while True:
        user_input = input("Você: ")
        if user_input.lower() == "sair":
            print("Encerrando a conversa.")
            break

        print("IA (pensando...):")
        resposta_ia = ia_financas.interagir(user_input)
        # Ajustado para imprimir apenas a resposta final do agente, evitando duplicação.
        # Os logs internos do agente (verbose=True) já mostram o processo de pensamento.
        print(f"IA: {resposta_ia}")

    # Opcional: Visualizar a planilha após a interação para ver se algo foi adicionado
    print("\n--- Dados Finais da Planilha ---")
    print(plan_manager.visualizar_dados(NomesAbas.TRANSACOES))


if __name__ == "__main__":
    main()
