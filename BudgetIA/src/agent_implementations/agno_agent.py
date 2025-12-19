from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools import Function

import config
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from core.base_tool import BaseTool

# Importa repositórios e loader
from finance.repositories.budget_repository import BudgetRepository
from finance.repositories.data_context import FinancialDataContext
from finance.repositories.debt_repository import DebtRepository
from finance.repositories.insight_repository import InsightRepository
from finance.repositories.profile_repository import ProfileRepository
from finance.repositories.transaction_repository import TransactionRepository
from finance.tool_loader import load_all_financial_tools

load_dotenv()

class AgnoAgent(AgentRunner):
    """
    Implementação do Agente usando o framework Agno (PhiData).
    """

    def __init__(
        self,
        llm_orchestrator: LLMOrchestrator,
        contexto_perfil: str,
        data_context: FinancialDataContext,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
        debt_repo: DebtRepository,
        profile_repo: ProfileRepository,
        insight_repo: InsightRepository,
    ) -> None:
        self.llm_orchestrator = llm_orchestrator
        
        # 1. Carrega o prompt do sistema
        try:
            with open(config.SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
                prompt_template_str = f.read()
        except FileNotFoundError:
            prompt_template_str = "Você é um assistente prestativo. {contexto_perfil}"

        self.system_prompt = prompt_template_str.format(
            contexto_perfil=contexto_perfil
        )

        # 2. Carrega as ferramentas customizadas
        tools_custom = load_all_financial_tools(
            data_context=data_context,
            transaction_repo=transaction_repo,
            budget_repo=budget_repo,
            debt_repo=debt_repo,
            profile_repo=profile_repo,
            insight_repo=insight_repo,
        )

        # 3. ADAPTOR: Converte BaseTool -> Agno Functions
        # O Agno aceita uma lista de funções no parâmetro 'tools'.
        # Vamos criar wrappers para o método .run() de cada ferramenta.
        self.agno_tools = []
        for tool in tools_custom:
            self.agno_tools.append(self._create_tool_wrapper(tool))

        # 4. Configura o Modelo (Gemini)
        # O LLMOrchestrator gerencia chaves e modelos, vamos pegar o nome do modelo dele
        # Mas instanciar a classe do Agno
        model_name = "gemini-1.5-flash" # Default seguro ou pegar do orchestrator
        # Tenta extrair o nome do modelo do orchestrator se possível, ou usa default
        # (Simplificação: vamos usar o default configurado no Agno para Gemini que geralmente é flash)
        
        # A chave de API deve estar no ambiente como GOOGLE_API_KEY, o Orchestrator garante isso via .env
        self.model = Gemini(id=model_name) 

        # 5. Inicializa o Agente
        self.agent = Agent(
            model=self.model,
            instructions=self.system_prompt, # Instructions = System Prompt
            tools=self.agno_tools,
            markdown=True,
            # add_history_to_context=True, # Gerencia histórico de sessão
            # show_tool_calls removido (não existe mais no init, usa-se debug_mode ou similar)
        )

    def _create_tool_wrapper(self, tool: BaseTool) -> Function:
        """
        Cria uma Agno Function que envolve o método .run() da BaseTool.
        Usa a classe Function para garantir que schemas e descrições sejam passados corretamente.
        """
        # Agno permite passar 'parameters' como um modelo Pydantic!
        # A nossa BaseTool já tem 'args_schema' que é um BaseModel.
        # Isso é perfeito.
        
        return Function(
            name=tool.name,
            description=tool.description,
            entrypoint=tool.run,
            parameters=tool.args_schema.model_json_schema(), # Passamos o JSON Schema!
        )

    def interagir(self, input_usuario: str) -> str:
        try:
            # O .print_response() do Agno imprime no console, nós queremos o retorno (string ou stream)
            # .run() retorna um objeto RunResponse
            response = self.agent.run(input_usuario)
            return response.content
        except Exception as e:
            print(f"ERRO AGNO: {e}")
            return f"Erro ao processar com Agno: {e}"

    @property
    def active_llm_info(self) -> str:
        return f"Agno Framework + {self.model.id}"

    @property
    def chat_history(self) -> list[dict[str, str]]:
        # O Agno gerencia histórico internamente (self.agent.memory)
        # Adaptar para o formato do Streamlit se necessário
        # Por simplicidade, retornamos vazio ou extraímos da memória do Agno
        return [] # TODO: Implementar conversão de memória Agno -> Streamlit

    @chat_history.setter
    def chat_history(self, history: list[dict[str, str]]) -> None:
        # TODO: Hydrate memory
        pass

    def add_message(self, role: str, content: str) -> None:
        pass
