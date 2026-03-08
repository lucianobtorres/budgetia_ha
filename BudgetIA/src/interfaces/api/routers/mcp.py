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
        
        # O mcp-python-sdk não tem um 'handle_single_request' oficial fácil de usar fora de streams,
        # mas podemos simular um stream de memória para obter a resposta.
        from anyio import create_memory_object_stream
        
        read_send, read_recv = create_memory_object_stream(1)
        write_send, write_recv = create_memory_object_stream(1)
        
        # Injeta o request no stream de leitura
        import json
        await read_send.send(json.dumps(body))
        
        # Executa o servidor em modo "one-shot"
        # Nota: Isso é um pouco hacky, mas funciona para transformar um SDK orientado a stream em request-reply
        import anyio
        async with anyio.create_task_group() as tg:
            tg.start_soon(mcp_app.server.run, read_recv, write_send, mcp_app.server.create_initialization_options())
            
            # Aguarda a resposta no stream de escrita
            # O primeiro JSON costuma ser o 'initialize' result ou erro, mas aqui o cliente envia o body direto
            # Se o corpo for um request direto, o SDK vai responder.
            raw_response = await write_recv.receive()
            tg.cancel_scope.cancel()
            
        return json.loads(raw_response)
        
    except Exception as e:
        logger.error(f"MCP RPC: Erro ao processar requisição HTTP: {e}")
        return {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None}

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
