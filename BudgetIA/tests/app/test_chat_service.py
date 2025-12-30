import pytest
from unittest.mock import MagicMock
from application.chat_service import ChatService
from core.agent_runner_interface import AgentRunner
from application.chat_history_manager import BaseHistoryManager

class MockAgentRunner(AgentRunner):
    def __init__(self):
        self.messages = []
    
    def interagir(self, user_input: str) -> str:
        return "Resposta Mock"

    def interact_with_details(self, user_input: str) -> dict:
        return {"output": "Resposta Mock", "intermediate_steps": []}
    
    @property
    def active_llm_info(self) -> str:
        return "Mock LLM"
    
    @property
    def chat_history(self) -> list[dict[str, str]]:
        return []
    
    @chat_history.setter
    def chat_history(self, history: list[dict[str, str]]) -> None:
        pass

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

def test_chat_service_add_first_message_uses_add_message():
    # Arrange
    mock_agent = MockAgentRunner()
    mock_history = MagicMock(spec=BaseHistoryManager)
    mock_history.get_history.return_value = [] # Histórico vazio
    
    service = ChatService(agent_runner=mock_agent, history_manager=mock_history)
    
    # Act
    service.add_first_message("Olá!")
    
    # Assert
    # Verifica se chamou o método da interface
    assert len(mock_agent.messages) == 1
    assert mock_agent.messages[0] == {"role": "assistant", "content": "Olá!"}
    
    # Verifica se adicionou ao histórico da UI
    mock_history.add_message.assert_called_with("assistant", "Olá!")

def test_chat_service_handle_message_flow():
    # Arrange
    mock_agent = MockAgentRunner()
    mock_history = MagicMock(spec=BaseHistoryManager)
    
    # Mock do CacheService para não falhar no rate limit
    from unittest.mock import patch
    with patch("application.chat_service.CacheService") as MockCache:
        mock_cache_instance = MockCache.return_value
        mock_cache_instance.check_rate_limit.return_value = False
        
        service = ChatService(agent_runner=mock_agent, history_manager=mock_history)
        
        # Act
        response = service.handle_message("Pergunta", "user123")
        
        # Assert
        assert response == "Resposta Mock"
        # Verifica chamadas no histórico
        mock_history.add_message.assert_any_call("user", "Pergunta")
        mock_history.add_message.assert_any_call("assistant", "Resposta Mock")
