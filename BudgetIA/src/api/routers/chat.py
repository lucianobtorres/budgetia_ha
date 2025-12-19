from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_agent_runner
from core.agent_runner_interface import AgentRunner

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"  # Preparação para multi-sessão


class ChatResponse(BaseModel):
    response: str
    history: list[dict[str, str]] | None = None


# Memória Temporária simples para API (Map session_id -> List[Messages])
# Idealmente o AgentRunner já gerencia isso, mas o 'LangChainAgent' tem memória interna.
# Vamos confiar na memória interna do Agente por enquanto ou injetar histórico.


@router.post("/message", response_model=ChatResponse)
def enviar_mensagem(
    request: ChatRequest, agent: AgentRunner = Depends(get_agent_runner)
) -> ChatResponse:
    """
    Simula uma interação de chat.
    Recebe mensagem, passa pro agente e retorna resposta.
    """
    try:
        print(f"--- API Chat: Recebido '{request.message}' ---")

        # O AgentRunner (IADeFinancas) já tem memória interna baseada no LangChain Memory
        # Para stateless real, deveríamos passar o histórico aqui.
        # Como estamos no MVP RAM, o 'agent' é singleton, então lembra da conversa.

        resposta = agent.interagir(request.message)

        # Opcional: Retornar histórico (se o adapter precisar re-renderizar)
        # history = agent.chat_history if hasattr(agent, 'chat_history') else []

        return ChatResponse(response=resposta)

    except Exception as e:
        print(f"Erro no endpoint de chat: {e}")
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
