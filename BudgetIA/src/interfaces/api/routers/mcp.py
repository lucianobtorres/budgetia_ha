from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from mcp.server.sse import SseServerTransport
from starlette.types import Scope, Receive, Send

from interfaces.api.dependencies import (
    get_planilha_manager,
    get_llm_orchestrator,
    get_memory_service,
    get_memory_service,
    get_mcp_user
)
from interfaces.mcp.server import BudgetIAMCPServer
from core.logger import get_logger

logger = get_logger("MCPRouter")
router = APIRouter(prefix="/mcp", tags=["MCP"])

# Mapa de transportes ativos por usuário
sse_transports: dict[str, SseServerTransport] = {}

@router.get("/sse")
async def sse(
    scope: Scope, receive: Receive, send: Send,
    plan_manager=Depends(get_planilha_manager),
    llm_orchestrator=Depends(get_llm_orchestrator),
    memory_service=Depends(get_memory_service),
    config_service=Depends(get_mcp_user)
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

    # Hand-off correto para o protocolo ASGI
    await handle_mcp_session(scope, receive, send)

@router.post("/messages")
async def messages(
    scope: Scope, receive: Receive, send: Send,
    config_service=Depends(get_mcp_user)
):
    """
    Endpoint para o cliente MCP enviar mensagens (POST) após conectar o SSE.
    """
    user_id = config_service.username
    transport = sse_transports.get(user_id)
    
    if not transport:
        # Se não houver transporte, precisamos retornar 404 via ASGI
        response = Response("Transporte não encontrado", status_code=404)
        await response(scope, receive, send)
        return
        
    # SseServerTransport.handle_post_message é um ASGI app
    await transport.handle_post_message(scope, receive, send)
