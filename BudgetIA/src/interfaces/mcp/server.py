import json
from typing import Any

import mcp.types as types
from mcp.server import Server

from core.logger import get_logger
from finance.planilha_manager import PlanilhaManager
from finance.tool_loader import load_all_financial_tools

logger = get_logger("MCPServer")


class BudgetIAMCPServer:
    def __init__(self, dependencies: dict[str, Any]):
        self.server = Server("BudgetIA")
        self.dependencies = dependencies
        self._setup_handlers()

    def _setup_handlers(self):
        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """Lista recursos disponíveis (Resumo Financeiro)."""
            return [
                types.Resource(
                    uri="budgetia://summary",
                    name="Resumo Financeiro Atual",
                    description="Saldo total, receitas e despesas do mês vigente.",
                    mimeType="application/json",
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Lê o conteúdo de um recurso."""
            if uri == "budgetia://summary":
                manager: PlanilhaManager = self.dependencies.get("plan_manager")
                if manager:
                    summary = manager.get_summary()
                    return json.dumps(summary, indent=2, ensure_ascii=False)
            raise ValueError(f"Recurso '{uri}' não encontrado.")

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """Lista todas as ferramentas financeiras disponíveis."""
            # Verifica se a planilha está disponível primeiro
            manager: PlanilhaManager = self.dependencies.get("plan_manager")
            if not manager or not manager.check_connection()[0]:
                logger.warning(
                    "MCP: Planilha não disponível. Injetando ferramenta de aviso."
                )
                return [
                    types.Tool(
                        name="status_planilha",
                        description="RETORNA O STATUS DA PLANILHA. Única ferramenta disponível quando a planilha não está configurada.",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                        },
                    )
                ]

            tools = self._get_budgetia_tools()
            mcp_tools = []

            for tool in tools:
                mcp_tools.append(
                    types.Tool(
                        name=tool.name,
                        description=tool.description,
                        inputSchema=tool.args_schema.model_json_schema(),
                    )
                )

            return mcp_tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Executa uma ferramenta financeira."""
            # 1. Verificação de Disponibilidade da Planilha
            manager: PlanilhaManager = self.dependencies.get("plan_manager")
            if not manager or not manager.check_connection()[0]:
                return [
                    types.TextContent(
                        type="text",
                        text="ERRO: Planilha não encontrada ou não configurada. Por favor, realize o onboarding no BudgetIA primeiro.",
                    )
                ]

            # 2. Busca a ferramenta
            tools = self._get_budgetia_tools()
            target_tool = next((t for t in tools if t.name == name), None)

            if not target_tool:
                raise ValueError(f"Ferramenta '{name}' não encontrada.")

            # 3. Execução
            try:
                args = arguments or {}
                # Validação via Pydantic (o args_schema da tool)
                validated_args = target_tool.args_schema(**args)

                logger.info(f"MCP Executando ferramenta: {name} com {args}")
                # Formata como JSON se for lista ou dict para o agente entender melhor
                if isinstance(result, (dict, list)):
                    text_output = json.dumps(result, indent=2, ensure_ascii=False)
                else:
                    text_output = str(result)

                return [types.TextContent(type="text", text=text_output)]
            except Exception as e:
                logger.error(f"Erro ao executar ferramenta MCP '{name}': {e}")
                return [
                    types.TextContent(
                        type="text", text=f"Erro na execução da ferramenta: {str(e)}"
                    )
                ]

    def _get_budgetia_tools(self):
        """Carrega as ferramentas usando o loader existente."""
        return load_all_financial_tools(
            manager=self.dependencies["plan_manager"],
            memory_service=self.dependencies["memory_service"],
            config_service=self.dependencies["config_service"],
            llm_orchestrator=self.dependencies["llm_orchestrator"],
            essential_only=False,  # No MCP podemos expor tudo
        )
