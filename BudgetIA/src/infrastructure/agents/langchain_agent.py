# src/agent_implementations/langchain_agent.py

import time
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import StructuredTool  # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # noqa: E402

import config  # noqa: E402
from core.agent_runner_interface import AgentRunner  # noqa: E402
from core.intelligence.fact_checker import FactChecker  # noqa: E402
from core.llm_manager import LLMOrchestrator  # noqa: E402
from core.memory.memory_service import MemoryService  # NEW  # noqa: E402
from core.user_config_service import UserConfigService  # NEW  # noqa: E402
from finance.planilha_manager import PlanilhaManager  # noqa: E402
from finance.tool_loader import load_all_financial_tools  # noqa: E402

load_dotenv()

from core.logger import get_logger  # noqa: E402

logger = get_logger("Agent")


class IADeFinancas(AgentRunner):  # type: ignore[misc]
    """
    Gerencia a comunicação com a API do LLM para gerar insights financeiros
    e interagir com a planilha usando ferramentas (via repositórios).
    """

    def __init__(
        self,
        llm_orchestrator: LLMOrchestrator,
        contexto_perfil: str,
        planilha_manager: PlanilhaManager,
        memory_service: MemoryService,
        config_service: UserConfigService,
    ) -> None:
        """
        Inicializa o modelo LLM, as ferramentas (via ToolLoader) e o agente LangChain.
        """
        start_init = time.time()
        # self.plan_manager = planilha_manager # REMOVIDO
        self.llm_orchestrator = llm_orchestrator
        self.memory_service = memory_service  # Store instance
        self.model = self.llm_orchestrator.get_current_llm()

        try:
            with open(config.SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
                prompt_template_str = f.read()
                logger.debug(
                    f"Verificando prompt carregado (primeiras 500 chars): {prompt_template_str[:500]}"
                )
        except FileNotFoundError:
            logger.error(
                f"Arquivo de prompt do sistema não encontrado em {config.SYSTEM_PROMPT_PATH}"
            )
            prompt_template_str = "Você é um assistente prestativo. {contexto_perfil}"

        final_system_prompt = prompt_template_str.format(
            contexto_perfil=contexto_perfil
        )

        # --- INJEÇÃO DE CHRONOS & MEMÓRIA ---
        # 1. Data Atual
        final_system_prompt = (
            "Data e Hora Atual: {data_atual}\n\n" + final_system_prompt
        )

        # 2. Injeção de Categorias Dinâmicas (Compacta)
        try:
            categories = planilha_manager.category_repo.list_all()
            if categories:
                # Se houver muitas, omitimos as tags para não poluir o prompt
                show_tags = len(categories) < 15
                lista_cats = [
                    f"- {c.name} ({c.type})"
                    + (
                        f" [Tags: {c.tags}]"
                        if show_tags and c.tags and c.tags != "nan"
                        else ""
                    )
                    for c in categories
                ]
                cats_str = (
                    ", ".join(lista_cats) if not show_tags else "\n".join(lista_cats)
                )
                msg_cats = f"\n\n=== CATEGORIAS DISPONÍVEIS ===\n{cats_str}\n=============================="
                final_system_prompt += msg_cats
        except Exception as e:
            logger.warning(f"Erro ao injetar categorias no prompt: {e}")

        # 3. Memória de Longo Prazo (Seletiva)
        memory_context = self.memory_service.get_context_string()
        if memory_context and len(memory_context) > 10:
            final_system_prompt += f"\n\n=== MEMÓRIA DE LONGO PRAZO ===\n{memory_context}\n=============================="

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", final_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        from langchain.memory import ConversationBufferWindowMemory

        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10,
            output_key="output",
            input_key="input",
        )

        logger.debug("Carregando ferramentas com injeção de repositório e memória...")
        tools_custom = load_all_financial_tools(
            manager=planilha_manager,
            memory_service=self.memory_service,
            config_service=config_service,
            llm_orchestrator=self.llm_orchestrator,
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
        logger.info(f"⏱️ Agente inicializado em {time.time() - start_init:.2f}s")

    def interagir(self, input_usuario: str) -> str:
        """Executa o agente e retorna apenas a string final (compatibilidade)."""
        result = self.interact_with_details(input_usuario)
        return result["output"]

    def interact_with_details(self, input_usuario: str) -> dict:
        """Executa o agente e retorna resposta + passos intermediários."""
        try:
            # Injeta a data atual na execução
            data_atual = datetime.now().strftime("%d/%m/%Y (%A) - %H:%M")

            start_invoke = time.time()
            response = self.agent_executor.invoke(
                {"input": input_usuario, "data_atual": data_atual}
            )
            logger.info(
                f"⏱️ AgentExecutor.invoke total: {time.time() - start_invoke:.2f}s"
            )

            output = str(response.get("output", "Não consegui processar sua solicitação."))
            steps = []

            if "intermediate_steps" in response:
                for action, observation in response["intermediate_steps"]:
                    steps.append(
                        {
                            "tool": action.tool,
                            "tool_input": action.tool_input,
                            "log": action.log,
                            "observation": str(observation),
                        }
                    )

            # 3. Chain of Verification (CoV) - Auditoria de Veracidade
            final_output = self._chain_of_verification(output, steps)

            return {"output": final_output, "intermediate_steps": steps}

        except Exception as e:
            logger.critical(f"ERRO CRÍTICO NO AGENTE: {e}", exc_info=True)
            return {
                "output": f"Desculpe, ocorreu um erro interno: {e}",
                "intermediate_steps": [],
            }

    def _chain_of_verification(self, output: str, steps: list[dict]) -> str:
        """
        Realiza uma auditoria avançada da resposta baseada nos passos intermediários.
        Utiliza o FactChecker para detectar e corrigir alucinações.
        """
        if not steps:
            return output

        return FactChecker.audit_and_fix(output, steps, self.llm_orchestrator)

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
