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
    scope: Scope, receive: Receive, send: Send,
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

    # Hand-off correto para o protocolo ASGI
    await handle_mcp_session(scope, receive, send)

@router.post("/rpc")
async def mcp_rpc(
    request: Request,
    plan_manager=Depends(get_planilha_manager),
    llm_orchestrator=Depends(get_llm_orchestrator),
    memory_service=Depends(get_memory_service),
    config_service=Depends(get_user_config_service)
):
    """
    Endpoint RPC via HTTP (POST). 
    Permite executar ferramentas MCP em uma única requisição (stateless),
    evitando problemas de proxy com SSE.
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
    
    # Processa o corpo JSON-RPC
    try:
        body = await request.json()
        logger.debug(f"MCP RPC: Recebida requisição de '{user_id}': {body.get('method')}")
        
        from mcp.shared.memory import create_memory_client_session
        from mcp.types import JSONRPCMessage, JSONRPCRequest, JSONRPCResponse, JSONRPCNotification
        import anyio
        
        # O MCP SDK espera um fluxo de objetos JSONRPCMessage.
        # Como o HTTP é stateless, fazemos um "kickstart" da sessão enviando:
        # 1. Initialize Request
        # 2. Initialized Notification
        # 3. A requisição real do usuário (body)
        
        async with create_memory_client_session(mcp_app.server) as session:
            # 1. Handshake Inicial
            await session.initialize()
            
            # 2. Converte o body do usuário em um objeto de request do MCP
            # Nota: O body vindo do script já está no formato JSON-RPC
            request_id = body.get("id", "1")
            method = body.get("method")
            params = body.get("params", {})
            
            # Executa a chamada conforme o método
            if method == "tools/list":
                result = await session.list_tools()
                return {"jsonrpc": "2.0", "result": result.model_dump(), "id": request_id}
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = await session.call_tool(tool_name, tool_args)
                return {"jsonrpc": "2.0", "result": result.model_dump(), "id": request_id}
            else:
                # Fallback para outros métodos genéricos via low-level request
                from mcp.types import JSONRPCRequest
                resp = await session.send_request(JSONRPCRequest(
                    method=method,
                    params=params,
                    id=request_id
                ))
                return {"jsonrpc": "2.0", "result": resp, "id": request_id}
                
    except Exception as e:
        logger.error(f"MCP RPC: Erro ao processar requisição HTTP: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": body.get("id") if 'body' in locals() else None}

@router.post("/messages")
async def messages(
    scope: Scope, receive: Receive, send: Send,
    config_service=Depends(get_user_config_service)
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
