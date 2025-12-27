# src/agent_implementations/langchain_agent.py

from datetime import datetime
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationSummaryBufferMemory
from langchain.tools import StructuredTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import config
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from core.memory.memory_service import MemoryService # NEW
from core.user_config_service import UserConfigService # NEW
from finance.repositories.budget_repository import BudgetRepository

# Importa todos os repositórios e o contexto
from finance.repositories.data_context import FinancialDataContext
from finance.repositories.debt_repository import DebtRepository
from finance.repositories.insight_repository import InsightRepository
from finance.repositories.profile_repository import ProfileRepository
from finance.repositories.transaction_repository import TransactionRepository
from finance.tool_loader import load_all_financial_tools

load_dotenv()


class IADeFinancas(AgentRunner):  # type: ignore[misc]
    """
    Gerencia a comunicação com a API do LLM para gerar insights financeiros
    e interagir com a planilha usando ferramentas (via repositórios).
    """

    def __init__(
        self,
        # planilha_manager: PlanilhaManager, # REMOVIDO
        llm_orchestrator: LLMOrchestrator,
        contexto_perfil: str,
        # --- NOVOS ARGUMENTOS (DIP) ---
        data_context: FinancialDataContext,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
        debt_repo: DebtRepository,
        profile_repo: ProfileRepository,
        insight_repo: InsightRepository,
        memory_service: MemoryService, # NEW Dependency
        config_service: UserConfigService, # NEW Dependency
        # --- FIM NOVOS ARGUMENTOS ---
    ) -> None:
        """
        Inicializa o modelo LLM, as ferramentas (via ToolLoader) e o agente LangChain.
        """
        # self.plan_manager = planilha_manager # REMOVIDO
        self.llm_orchestrator = llm_orchestrator
        self.memory_service = memory_service # Store instance
        self.model = self.llm_orchestrator.get_current_llm()

        try:
            with open(config.SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
                prompt_template_str = f.read()
                print(
                    f"--- DEBUG (Agent): Verificando prompt carregado (primeiras 500 chars): {prompt_template_str[:500]} ---"
                )
        except FileNotFoundError:
            print(
                f"ERRO: Arquivo de prompt do sistema não encontrado em {config.SYSTEM_PROMPT_PATH}"
            )
            prompt_template_str = "Você é um assistente prestativo. {contexto_perfil}"

        final_system_prompt = prompt_template_str.format(
            contexto_perfil=contexto_perfil
        )
        
        # --- INJEÇÃO DE CHRONOS & MEMÓRIA ---
        # 1. Data Atual
        final_system_prompt = "Data e Hora Atual: {data_atual}\n\n" + final_system_prompt
        
        # 2. Memória de Longo Prazo (Jarvis Mind)
        memory_context = self.memory_service.get_context_string()
        final_system_prompt += f"\n\n=== MEMÓRIA DE LONGO PRAZO ===\n{memory_context}\n=============================="

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", final_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.memory = ConversationSummaryBufferMemory(
            llm=llm_orchestrator.get_configured_llm(),
            max_token_limit=1024,
            memory_key="chat_history",
            return_messages=True,
            output_key="output",
            input_key="input",  # FIXED: Explicitly set input key
        )

        print("--- DEBUG AGENTE: Carregando ferramentas com injeção de repositório e memória...")
        tools_custom = load_all_financial_tools(
            # planilha_manager=planilha_manager, # REMOVIDO
            data_context=data_context,
            transaction_repo=transaction_repo,
            budget_repo=budget_repo,
            debt_repo=debt_repo,
            profile_repo=profile_repo,
            insight_repo=insight_repo,
            memory_service=self.memory_service, # PASS DEPENDENCY
            config_service=config_service, # PASS DEPENDENCY
            llm_orchestrator=self.llm_orchestrator, # PASS DEPENDENCY
        )

        self.tools = [
            StructuredTool.from_function(
                func=tool.run,
                name=tool.name,
                description=tool.description,
                args_schema=tool.args_schema,
            )
            for tool in tools_custom
        ]

        llm = self.llm_orchestrator.get_configured_llm()
        self.agent_executor = AgentExecutor(
            agent=create_tool_calling_agent(llm, self.tools, prompt_template),
            tools=self.tools,
            verbose=True,
            memory=self.memory,
            return_intermediate_steps=True,  # ENABLED
            handle_parsing_errors=True,
        )

    def interagir(self, input_usuario: str) -> str:
        """Executa o agente e retorna apenas a string final (compatibilidade)."""
        result = self.interact_with_details(input_usuario)
        return result["output"]

    def interact_with_details(self, input_usuario: str) -> dict:
        """Executa o agente e retorna resposta + passos intermediários."""
        try:
            # Injeta a data atual na execução
            data_atual = datetime.now().strftime("%d/%m/%Y (%A) - %H:%M")

            response = self.agent_executor.invoke({
                "input": input_usuario,
                "data_atual": data_atual
            })
            
            output = str(response.get("output", "Não consegui processar sua solicitação."))
            steps = []
            
            # Parse intermediate steps if present
            # Format: [(AgentAction, observation), ...]
            if "intermediate_steps" in response:
                for action, observation in response["intermediate_steps"]:
                    steps.append({
                        "tool": action.tool,
                        "tool_input": action.tool_input,
                        "log": action.log,
                        "observation": str(observation)
                    })

            return {"output": output, "intermediate_steps": steps}

        except Exception as e:
            print(f"ERRO CRÍTICO NO AGENTE: {e}")
            import traceback
            traceback.print_exc()
            return {"output": f"Desculpe, ocorreu um erro interno: {e}", "intermediate_steps": []}

    @property
    def active_llm_info(self) -> str:
        if not self.llm_orchestrator.active_llm_info:
            return "Nenhum LLM configurado"
        return str(self.llm_orchestrator.active_llm_info)

    @property
    def chat_history(self) -> list[dict[str, str]]:
        messages = self.memory.chat_memory.messages
        history: list[dict[str, str]] = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": str(msg.content)})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": str(msg.content)})
        return history

    @chat_history.setter
    def chat_history(self, history: list[dict[str, str]]) -> None:
        self.memory.clear()
        for item in history:
            if item["role"] == "user":
                self.memory.chat_memory.add_user_message(item["content"])
            elif item["role"] == "assistant":
                self.memory.chat_memory.add_ai_message(item["content"])

    def add_message(self, role: str, content: str) -> None:
        """Adiciona uma mensagem isolada à memória do agente."""
        if role == "user":
            self.memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            self.memory.chat_memory.add_ai_message(content)
