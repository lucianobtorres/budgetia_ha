# src/initialization/onboarding/analyzers.py
import json
import logging
from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import HumanMessage

from core.llm_manager import LLMOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Estrutura para armazenar o resultado da análise e tradução da planilha."""

    success: bool
    message: str  # Mensagem de sucesso ou o erro completo
    schema_summary: str  # df.info(), df.head() ou o esquema lido
    strategy_path: str | None = None  # Caminho do arquivo .py gerado em caso de sucesso


@dataclass
class UserProfile:
    financial_literacy: str  # "iniciante", "intermediario", "avancado"
    spending_habit: str  # "poupador", "gastador", "equilibrado"
    main_goal: str  # ex: "sair das dividas", "investir", "controlar gastos"


@dataclass
class FinancialStrategy:
    name: str
    description: str
    allocation: dict[
        str, float
    ]  # ex: {"Essenciais": 0.50, "Estilo de Vida": 0.30, "Investimentos": 0.20}


class ProfileAnalyzer:
    """
    Analisa o histórico de conversa para extrair o perfil financeiro do usuário.
    """

    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.llm = llm_orchestrator.get_current_llm()

    def analyze(self, chat_history: list[str]) -> UserProfile:
        """
        Processa o histórico de chat e retorna um perfil estruturado.
        """
        history_text = "\n".join(chat_history)

        prompt = f"""
        Analise a conversa de onboarding abaixo e extraia o perfil financeiro do usuário.
        Retorne APENAS um JSON válido com o seguinte formato, sem markdown ou explicações:
        {{
            "financial_literacy": "iniciante" | "intermediario" | "avancado",
            "spending_habit": "poupador" | "gastador" | "equilibrado",
            "main_goal": "resumo do objetivo principal identificado"
        }}

        Se não houver informação suficiente, infira "iniciante", "equilibrado" e "controle geral".

        CONVERSA:
        {history_text}
        """

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            # Limpeza básica caso o LLM retorne markdown ```json ... ```
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            return UserProfile(
                financial_literacy=data.get("financial_literacy", "iniciante"),
                spending_habit=data.get("spending_habit", "equilibrado"),
                main_goal=data.get("main_goal", "organizar finanças"),
            )
        except Exception as e:
            logger.error(f"Erro ao analisar perfil: {e}")
            # Fallback seguro
            return UserProfile("iniciante", "equilibrado", "organizar finanças")


class StrategySuggester:
    """
    Sugere estratégias financeiras com base no perfil.
    """

    def suggest(self, profile: UserProfile) -> FinancialStrategy:
        # Lógica simples baseada em regras (pode evoluir para LLM depois)

        if (
            profile.financial_literacy == "iniciante"
            or profile.main_goal.lower().find("dívida") != -1
        ):
            return FinancialStrategy(
                name="Método 50/30/20 (Simplificado)",
                description="Ideal para começar. 50% para Necessidades, 30% para Desejos, 20% para Poupança/Dívidas.",
                allocation={"Necessidades": 0.50, "Desejos": 0.30, "Poupança": 0.20},
            )

        elif profile.spending_habit == "gastador":
            return FinancialStrategy(
                name="Método 'Pague-se Primeiro'",
                description="Prioriza seus investimentos antes de gastar. Ideal para controlar impulsos.",
                allocation={"Investimentos (Prioridade)": 0.20, "Gastos Gerais": 0.80},
            )

        else:
            return FinancialStrategy(
                name="Regra 50/30/20 Clássica",
                description="O padrão ouro da organização financeira. Equilíbrio entre viver hoje e guardar para amanhã.",
                allocation={
                    "Necessidades": 0.50,
                    "Desejos": 0.30,
                    "Objetivos Financeiros": 0.20,
                },
            )
class UserIntent(Enum):
    POSITIVE_CONFIRMATION = "positive_confirmation"
    NEGATIVE_REFUSAL = "negative_refusal"
    SKIP = "skip"
    QUESTION = "question"
    NEUTRAL_INFO = "neutral_info"
    INTERVIEW_COMPLETE = "interview_complete"  # User signals they're done with questions
    UNCLEAR = "unclear"


class IntentClassifier:
    """
    Classifica a intenção do usuário com base no contexto da conversa.
    """

    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.llm = llm_orchestrator.get_current_llm()

    def classify(
        self, user_text: str, current_state_name: str, last_agent_message: str
    ) -> UserIntent:
        """
        Determina a intenção do usuário.
        """
        # Atalhos para performance e custo (casos óbvios)
        text_lower = user_text.lower().strip()
        if text_lower in ["pular", "pular perfil", "pular etapa", "pular / finalizar", "finalizar"]:
            return UserIntent.SKIP
        if text_lower in ["não", "nao", "não, obrigado", "nao, obrigado"]:
            return UserIntent.NEGATIVE_REFUSAL
        if text_lower in ["sim", "claro", "com certeza", "ok", "pode ser", "aceitar sugestão", "aceitar sugestao", "aceitar", "usar esta", "tudo certo", "tudo certo!", "confirmar", "prosseguir"]:
            return UserIntent.POSITIVE_CONFIRMATION
        
        if text_lower in ["preciso de ajuda", "ajuda", "socorro", "não entendi", "duvida", "dúvida", "tenho uma dúvida"]:
            return UserIntent.QUESTION

        # Sinais de conclusão de entrevista (Hardcoded para garantir funcionamento)
        if text_lower in ["pronto", "terminei", "acabei", "é só isso", "e so isso", "entendi tudo", "já respondi", "ja respondi", "vamos começar", "vamos comecar", "começar", "comecar", "iniciar", "ir para o sistema"]:
            return UserIntent.INTERVIEW_COMPLETE

        # Heurística de contexto: Se o agente sugeriu finalizar/começar e o usuário concordou
        if last_agent_message:
            last_msg_lower = last_agent_message.lower()
            if any(term in last_msg_lower for term in ["vamos começar", "iniciar", "finalizar", "ir para o sistema", "dashboard", "pronto para", "tudo certo"]):
                 if text_lower in ["sim", "ok", "claro", "pode ser", "vamos", "bora", "tá bom", "ta bom"]:
                     return UserIntent.INTERVIEW_COMPLETE

        prompt = f"""
        Atue como um classificador de intenção para um chat de onboarding financeiro.
        
        Contexto:
        - Estado Atual: {current_state_name}
        - Última msg do Agente: "{last_agent_message}"
        - Msg do Usuário: "{user_text}"
        
        Classifique a intenção do usuário em UMA das seguintes categorias:
        
        1. positive_confirmation: O usuário concorda, aceita, quer continuar, diz "sim", "ok", "bora", "começar", "aceito".
           IMPORTANTE: Se o estado for WELCOME e o usuário disser "vamos começar", "iniciar", é positive_confirmation.
        2. negative_refusal: O usuário recusa, diz "não", "não quero", "agora não", "deixa pra lá".
        3. skip: O usuário quer pular a etapa explicitamente ("pular", "ir para o fim").
        4. question: O usuário fez uma pergunta ou pediu explicação.
        5. neutral_info: O usuário está apenas respondendo uma pergunta do perfil (ex: "gasto muito", "sou iniciante") ou conversando normalmente sem confirmar/negar nada explicitamente.
        6. interview_complete: O usuário sinaliza que terminou a entrevista, está satisfeito, indica "pronto", "entendi", "obrigado e pronto", "é isso", "tudo certo, podemos avançar", demonstra conclusão natural da conversa.
           IMPORTANTE: Se o estado for OPTIONAL_PROFILE e o usuário disser "vamos começar", "ir para o sistema", "iniciar", é interview_complete.
        
        Retorne APENAS o nome da categoria (ex: positive_confirmation). Nada mais.
        """

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip().lower()

            # Mapeamento seguro
            if "positive" in content:
                return UserIntent.POSITIVE_CONFIRMATION
            if "negative" in content or "refusal" in content:
                return UserIntent.NEGATIVE_REFUSAL
            if "skip" in content:
                return UserIntent.SKIP
            if "question" in content:
                return UserIntent.QUESTION
            if "interview_complete" in content or "complete" in content:
                return UserIntent.INTERVIEW_COMPLETE
            if "neutral" in content:
                return UserIntent.NEUTRAL_INFO
            
            return UserIntent.UNCLEAR

        except Exception as e:
            logger.error(f"Erro na classificação de intenção: {e}")
            return UserIntent.UNCLEAR
