from unittest.mock import MagicMock
from infrastructure.agents.agno_agent import AgnoAgent
from core.llm_manager import LLMOrchestrator
from core.base_tool import BaseTool
from pydantic import BaseModel, Field

# Mock das dependências
class MockToolSchema(BaseModel):
    arg1: str = Field(description="Teste arg")

class MockTool(BaseTool):
    name = "mock_tool"
    description = "Uma ferramenta de teste"
    args_schema = MockToolSchema
    def run(self, arg1: str) -> str:
        return f"Executado com {arg1}"

def test_agno_agent_initialization():
    """Testa se o AgnoAgent inicializa corretamente e cria os wrappers."""
    # Mocks
    mock_llm = MagicMock(spec=LLMOrchestrator)
    mock_llm.get_current_llm.return_value = "gemini-flash"
    
    # Repositórios Mock (O Agent chama load_all_financial_tools que usa isso)
    # Para evitar carregar ferramentas reais e seus repositórios, vamos mockar load_all_financial_tools
    # Mas como load_all é importado dentro do agno_agent.py, precisaríamos de patch.
    # Alternativa: Passar Mocks para o init e confiar que o agente vai chamar load_all
    # O agente chama: tools_custom = load_all_financial_tools(...)
    
    # VAMOS MOCKAR o modulo 'finance.tool_loader'
    from unittest.mock import patch
    
    with patch("infrastructure.agents.agno_agent.load_all_financial_tools") as mock_loader:
        mock_loader.return_value = [MockTool()]
        
        # Instancia
        agent = AgnoAgent(
            llm_orchestrator=mock_llm,
            contexto_perfil="Perfil Teste",
            data_context=MagicMock(),
            transaction_repo=MagicMock(),
            budget_repo=MagicMock(),
            debt_repo=MagicMock(),
            profile_repo=MagicMock(),
            insight_repo=MagicMock(),
        )
        
        # Verifica se criou a ferramenta Agno
        assert len(agent.agno_tools) == 1
        agno_func = agent.agno_tools[0]
        
        # Verifica propriedades da função Agno (Function do Agno)
        # O objeto retornado é um agno.tools.Function
        assert agno_func.name == "mock_tool"
        assert agno_func.description == "Uma ferramenta de teste"
        assert agno_func.parameters == MockToolSchema.model_json_schema()
        
        # O modelo Gemini deve ter sido instanciado
        assert agent.model is not None
