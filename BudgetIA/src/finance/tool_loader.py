# Em: src/finance/tool_loader.py
import importlib
import inspect  # Importa o inspect
import os
from collections.abc import Callable  # Importa o que precisamos
from typing import Any

from core.base_tool import BaseTool
from core.logger import get_logger

logger = get_logger("ToolLoader")

# Importa todos os repositórios
from finance.repositories.budget_repository import BudgetRepository
from finance.repositories.data_context import FinancialDataContext
from finance.repositories.debt_repository import DebtRepository
from finance.repositories.insight_repository import InsightRepository
from finance.repositories.profile_repository import ProfileRepository
from finance.repositories.transaction_repository import TransactionRepository


from core.memory.memory_service import MemoryService # NEW
from core.user_config_service import UserConfigService # NEW

# Mapa de Traduções (Backend Source of Truth)
TOOL_TRANSLATIONS = {
    'add_transaction': 'Adicionar Transação',
    'adicionar_transacao': 'Adicionar Transação', # PT Key Support
    'add_debt': 'Adicionar Dívida', 
    'adicionar_divida': 'Adicionar Dívida', # PT Key Support
    'analyze_adherence': 'Analisar Aderência',
    'analisar_aderencia': 'Analisar Aderência', # PT Key Support
    'analyze_debt': 'Analisar Dívidas',
    'analisar_dividas': 'Analisar Dívidas', # PT Key Support
    'analyze_habits': 'Analisar Hábitos',
    'analisar_habitos': 'Analisar Hábitos', # PT Key Support
    'analyze_spending_trends': 'Tendências de Gastos',
    'analisar_tendencias_gastos': 'Tendências de Gastos', # PT Key Support
    'calculate_balance': 'Calcular Saldo',
    'calcular_saldo': 'Calcular Saldo', # PT Key Support
    'calculate_expenses_by_category': 'Despesas por Categoria',
    'calcular_despesas_por_categoria': 'Despesas por Categoria', # PT Key Support
    'check_budget_status': 'Status do Orçamento',
    'verificar_status_orcamento': 'Status do Orçamento', # PT Key Support
    'collect_user_profile': 'Coletar Perfil',
    'coletar_perfil_usuario': 'Coletar Perfil', # PT Key Support
    'define_budget': 'Definir Orçamento',
    'definir_orcamento': 'Definir Orçamento', # PT Key Support
    'delete_transaction': 'Excluir Transação',
    'excluir_transacao': 'Excluir Transação', # PT Key Support
    'extract_transactions': 'Extrair Transações',
    'extrair_transacoes': 'Extrair Transações', # PT Key Support
    'generate_monthly_summary': 'Resumo Mensal',
    'gerar_resumo_mensal': 'Resumo Mensal', # PT Key Support
    'identify_top_expenses': 'Maiores Despesas',
    'identificar_maiores_despesas': 'Maiores Despesas', # PT Key Support
    'memory_tools': 'Ferramentas de Memória',
    'recommend_rule': 'Recomendar Regras',
    'recomendar_regra': 'Recomendar Regras', # PT Key Support
    'register_ai_insight': 'Registrar Insight',
    'registrar_insight': 'Registrar Insight', # PT Key Support
    'rule_tools': 'Ferramentas de Regras',
    'update_transaction': 'Atualizar Transação',
    'atualizar_transacao': 'Atualizar Transação', # PT Key Support
    'view_data': 'Visualizar Dados',
    'visualizar_dados': 'Visualizar Dados', # PT Key Support
    'view_debts': 'Visualizar Dívidas',
    'visualizar_dividas': 'Visualizar Dívidas', # PT Key Support
    'visualizar_ultimas_transacoes': 'Últimas Transações',
    # Missing Keys identified by User
    'analisar_adesao_financeira': 'Analisar Adesão Financeira',
    'analisar_divida': 'Analisar Dívida',
    'calcular_saldo_total': 'Calcular Saldo Total',
    'create_spending_alert': 'Criar Alerta de Gastos',
    'extrair_transacoes_do_texto': 'Extrair Transações do Texto',
    'forget_user_fact': 'Esquecer Fato',
    'identificar_maiores_gastos': 'Identificar Maiores Gastos',
    'recomendar_regra_ideal': 'Recomendar Regra Ideal',
    'registrar_insight_ia': 'Registrar Insight',
    'visualizar_dados_planilha': 'Visualizar Dados Planilha',
}

def load_all_financial_tools(
    # planilha_manager: PlanilhaManager, # Removido
    data_context: FinancialDataContext,
    transaction_repo: TransactionRepository,
    budget_repo: BudgetRepository,
    debt_repo: DebtRepository,
    profile_repo: ProfileRepository,
    insight_repo: InsightRepository,
    memory_service: MemoryService,
    config_service: UserConfigService,
    llm_orchestrator: Any, # Injetado para ferramentas que precisam do LLM direto
    essential_only: bool = False, # Flag para carregar apenas ferramentas essenciais (Groq/Llama)
) -> list[BaseTool]:
    """
    Carrega dinamicamente todas as ferramentas financeiras do diretório 'tools/',
    injetando as dependências necessárias (métodos dos Repositórios)
    em seus construtores via Callable, usando 'inspect'.
    """
    tools_list: list[BaseTool] = []
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")



    # Lista de ferramentas essenciais para modelos menores (Llama 8B / Groq)
    ESSENTIAL_TOOLS_FILES = [
        "add_transaction_tool.py",
        "view_data_tool.py",
        "calculate_balance_tool.py",
        "check_budget_status_tool.py",
        "delete_transaction_tool.py", # CRUD
        "update_transaction_tool.py", # CRUD
        "generate_monthly_summary_tool.py",
        "register_ai_insight_tool.py",
        "define_budget_tool.py", # Importante para controle
        # Opcionais (Removidos para economizar tokens):
        # "extract_transactions_tool.py", # Complexo
        # "analyze_*.py", # Pesados
        # "memory_tools.py",
        # "debt_tools.py"
    ]

    # --- O MAPA DE DEPENDÊNCIAS (Sem PlanilhaManager) ---
    dependency_map: dict[str, Callable[..., Any]] = {
        # DataContext (Leitura genérica e salvamento)
        "view_data_func": data_context.get_dataframe,
        "save_func": data_context.save,
        # TransactionRepository
        "add_transaction_func": transaction_repo.add_transaction,
        "get_summary_func": transaction_repo.get_summary,
        "get_expenses_by_category_func": transaction_repo.get_expenses_by_category,
        # BudgetRepository
        "add_budget_func": budget_repo.add_or_update_budget,
        "recalculate_budgets_func": budget_repo.recalculate_all_budgets,
        # DebtRepository
        "add_debt_func": debt_repo.add_or_update_debt,
        # ProfileRepository
        "save_profile_func": profile_repo.save_profile_field,
        "get_profile_as_text_func": profile_repo.get_profile_as_text,
        # InsightRepository
        "register_insight_func": insight_repo.add_insight,
        # MemoryService
        "memory_service": memory_service,
        # UserConfigService
        "config_service": config_service,
        # LLM Orchestrator
        "llm_orchestrator": llm_orchestrator,
        # Repositories (Full Object Access)
        "transaction_repo": transaction_repo,
    }

    if not os.path.exists(tools_dir):
        logger.error(f"Diretório de ferramentas '{tools_dir}' não encontrado.")
        return tools_list

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            # Filtro de Essencial
            if essential_only and filename not in ESSENTIAL_TOOLS_FILES:
                continue

            module_name = filename[:-3]
            full_module_name = f"finance.tools.{module_name}"

            try:
                module = importlib.import_module(full_module_name)
                for attribute_name in dir(module):
                    attribute: Any = getattr(module, attribute_name)

                    if (
                        isinstance(attribute, type)
                        and issubclass(attribute, BaseTool)
                        and attribute is not BaseTool
                    ):
                        tool_class: type[BaseTool] = attribute

                        try:
                            tool_signature = inspect.signature(tool_class.__init__)
                            tool_params = tool_signature.parameters
                            kwargs_for_tool: dict[str, Any] = {}

                            for param_name in tool_params:
                                if param_name == "self":
                                    continue

                                if param_name in dependency_map:
                                    kwargs_for_tool[param_name] = dependency_map[
                                        param_name
                                    ]
                                else:
                                    logger.warning(
                                        f"Dependência '{param_name}' da ferramenta '{tool_class.__name__}' não encontrada no 'dependency_map'."
                                    )

                            tool_instance = tool_class(**kwargs_for_tool)
                            
                            # Inject Label (Translation)
                            tool_name_key = tool_instance.name.replace("_tool", "")
                            if tool_instance.name in TOOL_TRANSLATIONS:
                                tool_instance.label = TOOL_TRANSLATIONS[tool_instance.name]
                            elif tool_name_key in TOOL_TRANSLATIONS:
                                tool_instance.label = TOOL_TRANSLATIONS[tool_name_key]
                            else:
                                # Fallback: Title Case replacing underscores
                                tool_instance.label = tool_instance.name.replace("_", " ").title()

                            tools_list.append(tool_instance)

                        except TypeError as e:
                            logger.warning(
                                f"Não foi possível instanciar '{attribute_name}' do {full_module_name}. "
                                f"Verifique o __init__ e o 'dependency_map'. Erro: {e}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Erro inesperado ao carregar '{attribute_name}'. Erro: {e}"
                            )
            except Exception as e:
                logger.error(
                    f"Erro ao importar módulo '{full_module_name}'. Erro: {e}"
                )

    logger.info(f"{len(tools_list)} ferramentas carregadas com sucesso. (Essential Only: {essential_only})")
    return tools_list
