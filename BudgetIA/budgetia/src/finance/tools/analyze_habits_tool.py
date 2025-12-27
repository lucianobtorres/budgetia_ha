
from typing import Type
from pydantic import BaseModel, Field

from core.base_tool import BaseTool
from core.llm_manager import LLMOrchestrator
from core.memory.memory_service import MemoryService
from core.user_config_service import UserConfigService
from finance.repositories.transaction_repository import TransactionRepository
from application.services.behavior_analyst import BehaviorAnalyst


class AnalyzeHabitsInput(BaseModel):
    days: int = Field(60, description="Dias de histórico para analisar (Padrão: 60)")


class AnalyzeHabitsTool(BaseTool): # type: ignore[misc]
    """
    Ferramenta que aciona "O Observador" para analisar o histórico recente
    e aprender novos fatos sobre o comportamento financeiro do usuário.
    Gera memórias de longo prazo automaticamente.
    """

    name = "analyze_habits"
    description = (
        "Analisa os hábitos de gastos recentes para encontrar padrões ocultos. "
        "Use quando o usuário pedir 'O que você sabe sobre mim?' ou 'Analise meus gastos'."
    )
    args_schema: Type[BaseModel] = AnalyzeHabitsInput

    def __init__(
        self,
        llm_orchestrator: LLMOrchestrator,
        memory_service: MemoryService,
        transaction_repo: TransactionRepository,
    ):
        self.analyst = BehaviorAnalyst(llm_orchestrator, memory_service)
        self.transaction_repo = transaction_repo

    def run(self, days: int = 60) -> str:
        try:
            # Pegar dados brutos
            # O repo pode não ter get_all_dataframe, vamos usar o metodo publico
            # Assumindo que o tool loader injeta o repo correto que tem acesso ao DF
            df = self.transaction_repo.get_all_transactions()
            
            if df.empty:
                return "Não há transações suficientes para analisar."

            new_facts = self.analyst.analyze_recent_transactions(df, days)
            
            if not new_facts:
                return "Analisei seus gastos recentes mas não encontrei nenhum padrão novo ou significativo desta vez."
            
            lista_fatos = "\n".join([f"- {f}" for f in new_facts])
            return (
                f"🔎 Análise Concluída! Aprendi os seguintes fatos sobre você:\n\n{lista_fatos}\n\n"
                "Esses fatos foram salvos na minha memória de longo prazo."
            )

        except Exception as e:
            return f"Erro na análise de hábitos: {str(e)}"
