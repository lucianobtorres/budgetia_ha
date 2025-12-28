from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools import Function
from dotenv import load_dotenv

import config
from core.agent_runner_interface import AgentRunner
from core.base_tool import BaseTool
from core.llm_manager import LLMOrchestrator

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

        self.system_prompt = prompt_template_str.format(contexto_perfil=contexto_perfil)

        # 2. Configura o Modelo e Determina Provedor Ativo
        # Garante que o orchestrator já selecionou o provedor ativo (Gemini ou Fallback Groq)
        self.llm_orchestrator.get_configured_llm()
        active_provider = self.llm_orchestrator.active_provider_name

        print(f"--- AGNO AGENT: Configurando para provedor '{active_provider}' ---")

        # 3. Carrega as ferramentas customizadas (Com filtro Essential se for Groq)
        is_groq = active_provider == "groq"
        tools_custom = load_all_financial_tools(
            data_context=data_context,
            transaction_repo=transaction_repo,
            budget_repo=budget_repo,
            debt_repo=debt_repo,
            profile_repo=profile_repo,
            insight_repo=insight_repo,
            essential_only=is_groq,  # Filtra se for Groq para evitar Rate Limit (TPM)
        )

        # 4. ADAPTOR: Converte BaseTool -> Agno Functions
        # O Agno aceita uma lista de funções no parâmetro 'tools'.
        # Vamos criar wrappers para o método .run() de cada ferramenta.
        self.agno_tools = []
        for tool in tools_custom:
            self.agno_tools.append(self._create_tool_wrapper(tool))

        if active_provider == "groq":
            try:
                from agno.models.groq import Groq

                # Usa o modelo ativo do orchestrator ou um default do Groq
                model_id = (
                    self.llm_orchestrator.active_model_name or config.LLMModels.DEFAULT_GROQ
                )
                self.model = Groq(id=model_id)
            except ImportError:
                print(
                    "ERRO: 'agno.models.groq' não encontrado. Verifique se 'agno' está atualizado."
                )
                # Fallback para Gemini se der erro de import, mas provavelmente falhará se cota for o problema
                self.model = Gemini(id=config.LLMModels.GEMINI_2_5_FLASH)
        else:
            # Default: Gemini
            model_id = config.LLMModels.GEMINI_2_5_FLASH
            self.model = Gemini(id=model_id)

        # 5. Inicializa o Agente
        self.agent = Agent(
            model=self.model,
            instructions=self.system_prompt,  # Instructions = System Prompt
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
            parameters=tool.args_schema.model_json_schema(),  # Passamos o JSON Schema!
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

    def interact_with_details(self, input_usuario: str) -> dict:
        """
        Versão com detalhes para o Agno.
        Por enquanto retorna apenas a resposta padrão formatada.
        """
        response_text = self.interagir(input_usuario)
        return {"output": response_text, "intermediate_steps": []}

    @property
    def active_llm_info(self) -> str:
        return f"Agno Framework + {self.model.id}"

    @property
    def chat_history(self) -> list[dict[str, str]]:
        # O Agno gerencia histórico internamente (self.agent.memory)
        # Adaptar para o formato do Streamlit se necessário
        # Por simplicidade, retornamos vazio ou extraímos da memória do Agno
        return []  # TODO: Implementar conversão de memória Agno -> Streamlit

    @chat_history.setter
    def chat_history(self, history: list[dict[str, str]]) -> None:
        # TODO: Hydrate memory
        pass

    def add_message(self, role: str, content: str) -> None:
        pass
