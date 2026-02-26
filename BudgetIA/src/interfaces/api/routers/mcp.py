from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from mcp.server.sse import SseServerTransport
from starlette.types import Scope, Receive, Send

from interfaces.api.dependencies import (
    get_planilha_manager,
    get_llm_orchestrator,
    get_memory_service,
    get_user_config_service
)
from interfaces.mcp.server import BudgetIAMCPServer
from core.logger import get_logger

logger = get_logger("MCPRouter")
router = APIRouter(prefix="/mcp", tags=["MCP"])

# Mapa de transportes ativos por usuário
sse_transports: dict[str, SseServerTransport] = {}

@router.get("/sse")
async def sse(
    request: Request,
    plan_manager=Depends(get_planilha_manager),
    llm_orchestrator=Depends(get_llm_orchestrator),
    memory_service=Depends(get_memory_service),
    config_service=Depends(get_user_config_service)
):
    """
    Endpoint para conexão SSE do protocolo MCP.
    """
    user_id = config_service.username
    
    # Prepara dependências
    deps = {
        "data_context": plan_manager._context,
        "transaction_repo": plan_manager.transaction_repo,
        "budget_repo": plan_manager.budget_repo,
        "debt_repo": plan_manager.debt_repo,
        "profile_repo": plan_manager.profile_repo,
        "insight_repo": plan_manager.insight_repo,
        "memory_service": memory_service,
        "config_service": config_service,
        "llm_orchestrator": llm_orchestrator
    }

    mcp_app = BudgetIAMCPServer(deps)
    
    # Cria o transporte indicando a URL de POST mensagens
    # Nota: A URL deve ser absoluta ou relativa ao cliente. 
    # Usamos o caminho que registramos no FastAPI.
    transport = SseServerTransport("/api/mcp/messages")
    sse_transports[user_id] = transport

    # No FastAPI/Starlette, para rodar o transporte SSE que controla o send,
    # precisamos retornar uma resposta que execute o loop do MCP.
    
    async def handle_mcp_session(scope: Scope, receive: Receive, send: Send):
        async with transport.connect_sse(scope, receive, send) as (read_stream, write_stream):
            logger.info(f"MCP: Sessão iniciada para usuário '{user_id}'")
            try:
                await mcp_app.server.run(
                    read_stream, 
                    write_stream, 
                    mcp_app.server.create_initialization_options()
                )
            except Exception as e:
                logger.error(f"MCP: Erro na sessão do usuário '{user_id}': {e}")
            finally:
                logger.info(f"MCP: Sessão encerrada para usuário '{user_id}'")
                if user_id in sse_transports:
                    del sse_transports[user_id]

    return Response(content=None, status_code=200) # Placeholder, o Starlette handle_mcp_session deve ser chamado.

    # RETIFICANDO: A forma correta de injetar um handler ASGI no FastAPI 
    # é usar a própria app do transport se ela existir, ou chamar o connect_sse.
    # Como queremos integrar no Router, vamos usar o padrão de retornar o transport handler.
    
    # Vamos usar o EventSourceResponse do sse-starlette se o transport for compatível,
    # mas o mcp.server.sse.SseServerTransport.connect_sse é um ASGI middlware-like.
    
    # Versão simplificada que funciona com FastAPI:
    return Response(content=handle_mcp_session, media_type="text/event-stream")
