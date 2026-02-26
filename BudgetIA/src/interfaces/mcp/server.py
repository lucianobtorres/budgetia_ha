import json
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent, EmbeddedResource
import mcp.types as types
from pydantic import BaseModel

from core.logger import get_logger
from finance.tool_loader import load_all_financial_tools
from finance.repositories.data_context import FinancialDataContext

logger = get_logger("MCPServer")

class BudgetIAMCPServer:
    def __init__(self, dependencies: Dict[str, Any]):
        self.server = Server("BudgetIA")
        self.dependencies = dependencies
        self._setup_handlers()
        
    def _setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """Lista todas as ferramentas financeiras disponíveis."""
            # Verifica se a planilha está disponível primeiro
            data_context: FinancialDataContext = self.dependencies.get("data_context")
            if not data_context or not data_context.storage.ping()[0]:
                logger.warning("MCP: Planilha não disponível. Retornando lista vazia ou erro informativo.")
                # No MCP, podemos retornar ferramentas, mas a execução falhará.
                # Ou podemos injetar uma 'ferramenta de erro' ou simplesmente retornar o que temos.
                # Vamos injetar uma mensagem na descrição se não estiver disponível.
            
            tools = self._get_budgetia_tools()
            mcp_tools = []
            
            for tool in tools:
                mcp_tools.append(types.Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.args_schema.model_json_schema()
                ))
            
            return mcp_tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Executa uma ferramenta financeira."""
            # 1. Verificação de Disponibilidade da Planilha
            data_context: FinancialDataContext = self.dependencies.get("data_context")
            if not data_context or not data_context.storage.ping()[0]:
                return [types.TextContent(
                    type="text",
                    text="ERRO: Planilha não encontrada ou não configurada. Por favor, realize o onboarding no BudgetIA primeiro."
                )]

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
                result = target_tool.run(**validated_args.model_dump())
                
                return [types.TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.error(f"Erro ao executar ferramenta MCP '{name}': {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Erro na execução da ferramenta: {str(e)}"
                )]

    def _get_budgetia_tools(self):
        """Carrega as ferramentas usando o loader existente."""
        return load_all_financial_tools(
            data_context=self.dependencies["data_context"],
            transaction_repo=self.dependencies["transaction_repo"],
            budget_repo=self.dependencies["budget_repo"],
            debt_repo=self.dependencies["debt_repo"],
            profile_repo=self.dependencies["profile_repo"],
            insight_repo=self.dependencies["insight_repo"],
            memory_service=self.dependencies["memory_service"],
            config_service=self.dependencies["config_service"],
            llm_orchestrator=self.dependencies["llm_orchestrator"],
            essential_only=False # No MCP podemos expor tudo
        )
