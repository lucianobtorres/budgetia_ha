from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationSummaryBufferMemory
from langchain.tools import StructuredTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import config
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from finance.planilha_manager import PlanilhaManager
from finance.tool_loader import load_all_financial_tools

load_dotenv()


class IADeFinancas(AgentRunner):  # type: ignore[misc]
    """
    Gerencia a comunicação com a API do LLM para gerar insights financeiros
    e interagir com a planilha usando ferramentas, implementando a interface AgentRunner.
    """

    def __init__(
        self,
        planilha_manager: PlanilhaManager,
        llm_orchestrator: LLMOrchestrator,
        contexto_perfil: str,
    ) -> None:
        """
        Inicializa o modelo LLM (via orquestrador), as ferramentas e o agente LangChain.
        """
        self.plan_manager = planilha_manager
        self.llm_orchestrator = llm_orchestrator

        self.llm_orchestrator = llm_orchestrator
        self.model = self.llm_orchestrator.get_current_llm()

        # --- Carregamento do Prompt Externo ---
        # 1. Obter o contexto do perfil ANTES de criar o prompt
        # contexto_perfil = self.plan_manager.get_perfil_como_texto()
        # print(f"--- DEBUG AGENTE: Contexto do Perfil injetado: {contexto_perfil} ---")
        try:
            with open(config.SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
                prompt_template_str = f.read()
        except FileNotFoundError:
            print(
                f"ERRO: Arquivo de prompt do sistema não encontrado em {config.SYSTEM_PROMPT_PATH}"
            )
            prompt_template_str = (
                "Você é um assistente prestativo. {contexto_perfil}"  # Fallback
            )

        # 2. Formatar o template com o contexto
        final_system_prompt = prompt_template_str.format(
            contexto_perfil=contexto_perfil
        )

        # 3. Usar o prompt final formatado
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", final_system_prompt),  # <-- USA A STRING FORMATADA
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.memory = ConversationSummaryBufferMemory(
            llm=llm_orchestrator.get_configured_llm(),  # Passa o LLM para sumarizar
            max_token_limit=1024,  # Limite de tokens da memória
            memory_key="chat_history",
            return_messages=True,
            output_key="output",  # Garante que a saída do agente seja rastreada
        )

        tools_custom = load_all_financial_tools(planilha_manager)
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
            return_intermediate_steps=False,  # Opcional, mas limpa o log
            handle_parsing_errors=True,  # Lida com erros de formatação
        )

    def interagir(self, input_usuario: str) -> str:
        """Executa o agente com a entrada do usuário."""
        try:
            # O AgentExecutor com memória lida com o histórico automaticamente
            response = self.agent_executor.invoke({"input": input_usuario})
            return str(
                response.get("output", "Não consegui processar sua solicitação.")
            )
        except Exception as e:
            print(f"ERRO CRÍTICO NO AGENTE: {e}")
            import traceback

            traceback.print_exc()
            return f"Desculpe, ocorreu um erro interno: {e}"

    @property
    def active_llm_info(self) -> str:
        """
        Retorna uma string com o nome do provedor e modelo LLM ativos
        sendo usados por este agente, acessando do orquestrador.
        """
        if not self.llm_orchestrator.active_llm_info:
            return "Nenhum LLM configurado"
        return str(self.llm_orchestrator.active_llm_info)

    @property
    def chat_history(self) -> list[dict[str, str]]:
        # O getter agora lê da memória
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
        # O setter agora popula a memória com o histórico vindo do Streamlit
        self.memory.clear()
        for item in history:
            if item["role"] == "user":
                self.memory.chat_memory.add_user_message(item["content"])
            elif item["role"] == "assistant":
                self.memory.chat_memory.add_ai_message(item["content"])
