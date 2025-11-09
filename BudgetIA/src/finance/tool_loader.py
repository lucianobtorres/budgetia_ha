# Em: src/finance/tool_loader.py
import importlib
import inspect  # Importa o inspect
import os
from collections.abc import Callable  # Importa o que precisamos
from typing import Any

from core.base_tool import BaseTool

# Importa todos os repositórios
from finance.repositories.budget_repository import BudgetRepository
from finance.repositories.data_context import FinancialDataContext
from finance.repositories.debt_repository import DebtRepository
from finance.repositories.insight_repository import InsightRepository
from finance.repositories.profile_repository import ProfileRepository
from finance.repositories.transaction_repository import TransactionRepository


def load_all_financial_tools(
    # planilha_manager: PlanilhaManager, # Removido
    data_context: FinancialDataContext,
    transaction_repo: TransactionRepository,
    budget_repo: BudgetRepository,
    debt_repo: DebtRepository,
    profile_repo: ProfileRepository,
    insight_repo: InsightRepository,
) -> list[BaseTool]:
    """
    Carrega dinamicamente todas as ferramentas financeiras do diretório 'tools/',
    injetando as dependências necessárias (métodos dos Repositórios)
    em seus construtores via Callable, usando 'inspect'.
    """
    tools_list: list[BaseTool] = []
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")

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
    }

    if not os.path.exists(tools_dir):
        print(f"ERRO: Diretório de ferramentas '{tools_dir}' não encontrado.")
        return tools_list

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename != "__init__.py":
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
                        tool_class: Type[BaseTool] = attribute

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
                                    print(
                                        f"AVISO (ToolLoader): Dependência '{param_name}' da ferramenta '{tool_class.__name__}' não encontrada no 'dependency_map'."
                                    )

                            tool_instance = tool_class(**kwargs_for_tool)
                            tools_list.append(tool_instance)

                        except TypeError as e:
                            print(
                                f"AVISO (ToolLoader): Não foi possível instanciar '{attribute_name}' do {full_module_name}. "
                                f"Verifique o __init__ e o 'dependency_map'. Erro: {e}"
                            )
                        except Exception as e:
                            print(
                                f"ERRO (ToolLoader): Erro inesperado ao carregar '{attribute_name}'. Erro: {e}"
                            )
            except Exception as e:
                print(
                    f"ERRO (ToolLoader): Erro ao importar módulo '{full_module_name}'. Erro: {e}"
                )

    print(f"LOG (ToolLoader): {len(tools_list)} ferramentas carregadas com sucesso.")
    return tools_list
