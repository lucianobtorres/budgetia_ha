import importlib
import os

from core.base_tool import BaseTool
from finance.planilha_manager import (
    PlanilhaManager,
)


def load_all_financial_tools(planilha_manager: PlanilhaManager) -> list[BaseTool]:
    """
    Carrega dinamicamente todas as ferramentas financeiras definidas no diretório 'tools/'.
    Cada ferramenta deve herdar de BaseTool.
    """
    tools_list: list[BaseTool] = []
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")

    # Certifique-se de que o diretório 'tools' existe
    if not os.path.exists(tools_dir):
        print(f"ERRO: Diretório de ferramentas '{tools_dir}' não encontrado.")
        return tools_list

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]  # Remove .py
            full_module_name = (
                f"finance.tools.{module_name}"  # Caminho completo do módulo
            )

            try:
                module = importlib.import_module(full_module_name)
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if (
                        isinstance(attribute, type)
                        and issubclass(attribute, BaseTool)
                        and attribute is not BaseTool
                    ):
                        # Se for uma classe que herda de BaseTool (e não é a própria BaseTool)
                        try:
                            # Instancia a tool, passando o planilha_manager se necessário
                            # O construtor da tool deve estar preparado para isso
                            tool_instance = attribute(planilha_manager=planilha_manager)
                            tools_list.append(tool_instance)
                            print(
                                f"LOG: Ferramenta '{tool_instance.name}' carregada dinamicamente de {full_module_name}."
                            )
                        except TypeError as e:
                            print(
                                f"AVISO: Não foi possível instanciar a ferramenta '{attribute_name}' do módulo {full_module_name}. Erro: {e}. Verifique o __init__ da tool."
                            )
                        except Exception as e:
                            print(
                                f"ERRO: Erro inesperado ao carregar a ferramenta '{attribute_name}' do módulo {full_module_name}. Erro: {e}"
                            )
            except Exception as e:
                print(
                    f"ERRO: Erro ao importar módulo de ferramenta '{full_module_name}'. Erro: {e}"
                )

    return tools_list
