# src/initialization/onboarding/analyzers.py
import json
import logging
from dataclasses import dataclass

from langchain_core.messages import HumanMessage

from core.llm_manager import LLMOrchestrator

logger = logging.getLogger(__name__)


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
