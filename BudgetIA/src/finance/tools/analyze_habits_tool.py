import pandas as pd
from pydantic import BaseModel, Field

from application.services.behavior_analyst import BehaviorAnalyst
from core.base_tool import BaseTool
from core.llm_manager import LLMOrchestrator
from core.memory.memory_service import MemoryService
from finance.domain.repositories.transaction_repository import ITransactionRepository


class AnalyzeHabitsInput(BaseModel):
    days: int = Field(60, description="Dias de histórico para analisar (Padrão: 60)")


class AnalyzeHabitsTool(BaseTool):  # type: ignore[misc]
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
    args_schema: type[BaseModel] = AnalyzeHabitsInput

    def __init__(
        self,
        llm_orchestrator: LLMOrchestrator,
        memory_service: MemoryService,
        transaction_repo: ITransactionRepository,
    ):
        self.analyst = BehaviorAnalyst(llm_orchestrator, memory_service)
        self.transaction_repo = transaction_repo

    def run(self, days: int = 60) -> str:
        try:
            # Pegar dados brutos e converter para DF
            transactions = self.transaction_repo.list_all()
            if not transactions:
                return "Não há transações suficientes para analisar."

            # Converte lista de entidades para lista de dicts e então para DataFrame
            data = []
            for t in transactions:
                data.append(
                    {
                        "Data": t.data,
                        "Tipo": t.tipo,
                        "Categoria": t.categoria,
                        "Descricao": t.descricao,
                        "Valor": t.valor,
                        "Status": t.status,
                    }
                )
            df = pd.DataFrame(data)

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
