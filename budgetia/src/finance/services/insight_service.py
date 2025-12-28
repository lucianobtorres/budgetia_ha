# Em: src/finance/services/insight_service.py
from datetime import datetime
from typing import Any

import pandas as pd

from config import ColunasOrcamentos, NomesAbas

from ..repositories.budget_repository import BudgetRepository
from ..repositories.insight_repository import InsightRepository
from ..repositories.transaction_repository import TransactionRepository


class InsightService:
    """
    Classe especialista em realizar cálculos financeiros puros.
    Não possui estado e não conhece a planilha.
    """

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
        insight_repo: InsightRepository,
    ) -> None:
        """
        Inicializa o serviço com os repositórios necessários para a orquestração.
        """
        self._transaction_repo = transaction_repo
        self._budget_repo = budget_repo
        self._insight_repo = insight_repo

    def gerar_analise_proativa(
        self, orcamentos_df: pd.DataFrame, saldo_total: float
    ) -> list[dict[str, Any]]:
        """Gera insights proativos com base no status do orçamento."""
        insights: list = []
        if orcamentos_df.empty or ColunasOrcamentos.STATUS not in orcamentos_df.columns:
            return insights

        # --- CORREÇÃO (Falha 4) ---
        # Procura por "Estourado" (que é o que 'calcular_status_orcamentos' gera)
        orcamentos_estourados = orcamentos_df[
            orcamentos_df[ColunasOrcamentos.STATUS] == "Estourado"
        ]
        for _, row in orcamentos_estourados.iterrows():
            insights.append(
                {
                    "tipo_insight": "Alerta de Orçamento",
                    "titulo_insight": f"Orçamento Estourado: {row[ColunasOrcamentos.CATEGORIA]}",
                    "detalhes_recomendacao": f"Você ultrapassou o limite de R$ {row[ColunasOrcamentos.LIMITE]:,.2f} para {row[ColunasOrcamentos.CATEGORIA]}, gastando R$ {row[ColunasOrcamentos.GASTO]:,.2f}. Recomendo revisar seus gastos nesta categoria.",
                }
            )

        # --- CORREÇÃO (Falha 4) ---
        # Procura por "Alerta"
        orcamentos_alerta = orcamentos_df[
            orcamentos_df[ColunasOrcamentos.STATUS] == "Alerta"
        ]
        for _, row in orcamentos_alerta.iterrows():
            insights.append(
                {
                    "tipo_insight": "Aviso de Orçamento",
                    "titulo_insight": f"Orçamento em Alerta: {row[ColunasOrcamentos.CATEGORIA]}",
                    "detalhes_recomendacao": f"Você está próximo do limite de R$ {row[ColunasOrcamentos.LIMITE]:,.2f} para {row[ColunasOrcamentos.CATEGORIA]}, já gastou R$ {row[ColunasOrcamentos.GASTO]:,.2f} ({row[ColunasOrcamentos.PERCENTUAL]:.1f}%). Atenção aos próximos gastos.",
                }
            )
        # --- FIM DA CORREÇÃO ---

        if saldo_total < 0:
            insights.append(
                {
                    "tipo_insight": "Alerta de Saldo",
                    "titulo_insight": "Saldo Negativo",
                    "detalhes_recomendacao": f"Seu saldo total está negativo em R$ {saldo_total:,.2f}. É crucial revisar suas receitas e despesas para evitar dívidas.",
                }
            )

        # --- CORREÇÃO (Falha 5) ---
        # Adiciona insight "saudável" se não houver alertas
        if not insights and saldo_total > 0:
            insights.append(
                {
                    "tipo_insight": "Sugestão de Economia",
                    "titulo_insight": "Parabéns pelo Saldo Positivo!",
                    "detalhes_recomendacao": f"Seu saldo este mês está positivo em R$ {saldo_total:,.2f} e seus orçamentos estão sob controle. Considere investir ou poupar parte desse valor.",
                }
            )
        # --- FIM DA CORREÇÃO ---

        return insights

    def run_proactive_analysis_orchestration(self) -> list[dict[str, Any]]:
        """
        Orquestra todo o processo de análise proativa.
        (Lógica movida de PlanilhaManager.analisar_para_insights_proativos)
        """
        print("LOG (InsightService): Orquestrando análise proativa...")

        # 1. Recalcular orçamentos (garante que os dados estão frescos)
        self._budget_repo.recalculate_all_budgets()

        # 2. Buscar dados de transações (resumo)
        resumo = self._transaction_repo.get_summary()
        saldo_total = resumo.get("saldo", 0.0)

        # 3. Buscar dados de orçamentos (atualizados)
        orcamentos_df = self._budget_repo._context.get_dataframe(NomesAbas.ORCAMENTOS)

        # 4. Gerar os insights (lógica pura que já estava aqui)
        insights_gerados = self.gerar_analise_proativa(orcamentos_df, saldo_total)

        # 5. Salvar os insights no repositório
        if insights_gerados:
            print(
                f"LOG (InsightService): {len(insights_gerados)} insights gerados. Registrando..."
            )
            for insight in insights_gerados:
                self._insight_repo.add_insight(
                    data_insight=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    tipo_insight=insight["tipo_insight"],
                    titulo_insight=insight["titulo_insight"],
                    detalhes_recomendacao=insight["detalhes_recomendacao"],
                )
        else:
            print(
                "LOG (InsightService): Análise proativa concluída. Nenhum insight novo gerado."
            )

        return insights_gerados
