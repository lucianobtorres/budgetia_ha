from datetime import datetime
from typing import Any

from core.logger import get_logger

from ...domain.models.insight import Insight
from ...domain.repositories.budget_repository import IBudgetRepository
from ...domain.repositories.insight_repository import IInsightRepository
from ...domain.repositories.transaction_repository import ITransactionRepository

logger = get_logger("GenerateProactiveInsightsUseCase")


class GenerateProactiveInsightsUseCase:
    """
    Caso de Uso: Analisa a situação financeira atual e gera insights proativos (avisos, alertas, incentivos).
    """

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        budget_repo: IBudgetRepository,
        insight_repo: IInsightRepository,
    ):
        self._transaction_repo = transaction_repo
        self._budget_repo = budget_repo
        self._insight_repo = insight_repo

    def execute(self) -> list[dict[str, Any]]:
        """
        Orquestra a geração de insights.
        """
        logger.info("Executando análise proativa para geração de insights...")

        # 1. Recalcular orçamentos para garantir dados frescos
        self._budget_repo.recalculate_all_budgets()

        # 2. Calcular saldo total
        transactions = self._transaction_repo.list_all()
        receitas = sum(tx.valor for tx in transactions if not tx.eh_despesa)
        despesas = sum(tx.valor for tx in transactions if tx.eh_despesa)
        saldo_total = receitas - despesas

        # 3. Analisar status dos orçamentos via Data Context (ou Repositório se preferir)
        # Como o InsightService legado usava o DataFrame de orçamentos, vamos manter por enquanto
        # para preservar a lógica exata de "Alerta/Estourado" que já funciona.
        # TODO: Refatorar para usar Entidades de Budget no futuro.

        # Acesso seguro via context se disponível no repo concreto
        # No IBudgetRepository não temos get_dataframe, então vamos assumir que o domínio
        # de orçamento já possui o que precisamos se usarmos list_all?
        # Por simplicidade de migração agora, vamos usar a lógica do orcamentos_df se pudermos.

        # Se o repositório for o ExcelBudgetRepository, ele tem acesso ao context.
        # Mas vamos tentar ser o mais agnóstico possível.

        insights_gerados = []

        # Para cada orçamento, verificar status
        budgets = self._budget_repo.list_all()
        for b in budgets:
            if b.status == "Estourado":
                insights_gerados.append(
                    {
                        "tipo_insight": "Alerta de Orçamento",
                        "titulo_insight": f"Orçamento Estourado: {b.categoria}",
                        "detalhes_recomendacao": f"Você ultrapassou o limite de R$ {b.limite:,.2f} para {b.categoria}, gastando R$ {b.gasto:,.2f}. Recomendo revisar seus gastos nesta categoria.",
                    }
                )
            elif b.status == "Alerta":
                insights_gerados.append(
                    {
                        "tipo_insight": "Aviso de Orçamento",
                        "titulo_insight": f"Orçamento em Alerta: {b.categoria}",
                        "detalhes_recomendacao": f"Você está próximo do limite de R$ {b.limite:,.2f} para {b.categoria}, já gastou R$ {b.gasto:,.2f}. Atenção aos próximos gastos.",
                    }
                )

        if saldo_total < 0:
            insights_gerados.append(
                {
                    "tipo_insight": "Alerta de Saldo",
                    "titulo_insight": "Saldo Negativo",
                    "detalhes_recomendacao": f"Seu saldo total está negativo em R$ {saldo_total:,.2f}. É crucial revisar suas receitas e despesas para evitar dívidas.",
                }
            )
        elif not insights_gerados and saldo_total > 0:
            insights_gerados.append(
                {
                    "tipo_insight": "Sugestão de Economia",
                    "titulo_insight": "Parabéns pelo Saldo Positivo!",
                    "detalhes_recomendacao": f"Seu saldo este mês está positivo em R$ {saldo_total:,.2f} e seus orçamentos estão sob controle. Considere investir ou poupar parte desse valor.",
                }
            )

        # 4. Salvar os novos insights
        if insights_gerados:
            for item in insights_gerados:
                new_insight = Insight(
                    date=datetime.now(),
                    type=item["tipo_insight"],
                    title=item["titulo_insight"],
                    details=item["detalhes_recomendacao"],
                    status="Novo",
                )
                self._insight_repo.save(new_insight)
            logger.info(f"{len(insights_gerados)} novos insights gerados e salvos.")

        return insights_gerados
