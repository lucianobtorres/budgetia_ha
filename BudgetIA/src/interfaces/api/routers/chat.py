from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from interfaces.api.dependencies import get_agent_runner
from core.agent_runner_interface import AgentRunner

from core.logger import get_logger

logger = get_logger("API_Chat")

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"  # Preparação para multi-sessão


class ChatResponse(BaseModel):
    response: str
    history: list[dict[str, str]] | None = None
    intermediate_steps: list[dict] | None = None


# Memória Temporária simples para API (Map session_id -> List[Messages])
# Idealmente o AgentRunner já gerencia isso, mas o 'LangChainAgent' tem memória interna.
# Vamos confiar na memória interna do Agente por enquanto ou injetar histórico.


@router.post("/message", response_model=ChatResponse)
def enviar_mensagem(
    request: ChatRequest, agent: AgentRunner = Depends(get_agent_runner)
) -> ChatResponse:
    """
    Simula uma interação de chat.
    Recebe mensagem, passa pro agente e retorna resposta com passos (se houver).
    """
    try:
        logger.info(f"Recebido '{request.message}'")

        # Chama a verso detalhada
        result = agent.interact_with_details(request.message)
        
        # O resultado esperado é {"output": str, "intermediate_steps": list}
        resposta = result.get("output", "Sem resposta.")
        steps = result.get("intermediate_steps", [])

        return ChatResponse(response=resposta, intermediate_steps=steps)

    except Exception as e:
        logger.error(f"Erro no endpoint de chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
def limpar_historico(agent: AgentRunner = Depends(get_agent_runner)) -> dict[str, str]:
    """Limpa a memória do agente."""
    try:
        # Tenta limpar memória se o agente suportar
        if hasattr(agent, "memory") and hasattr(agent.memory, "clear"):
            agent.memory.clear()

        # Se tiver chat_history setter
        if hasattr(agent, "chat_history"):
            agent.chat_history = []

        return {"message": "Histórico limpo com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def obter_historico(agent: AgentRunner = Depends(get_agent_runner)) -> list[dict[str, str]]:
    """Retorna o histórico de mensagens da sessão atual."""
    try:
        # Tenta pegar memory.chat_memory.messages (LangChain standard)
        if hasattr(agent, "memory") and hasattr(agent.memory, "chat_memory"):
            messages = agent.memory.chat_memory.messages
            history = []
            for msg in messages:
                role = "user" if msg.type == "human" else "assistant"
                history.append({"role": role, "content": msg.content})
            return history
            
        # Fallback para atributo chat_history simples
        if hasattr(agent, "chat_history"):
             return agent.chat_history # type: ignore[no-any-return]

        return []
    except Exception as e:
        logger.error(f"Erro ao recuperar histórico: {e}")
        # Retorna lista vazia em caso de erro pra não quebrar UI
        return []
