# src/application/notifications/rules/economy/semantic_anomaly_rule.py
from typing import Any

import pandas as pd

import config
from application.notifications.models.notification_message import NotificationPriority
from application.notifications.models.rule_result import RuleResult
from application.notifications.rules.base_rule import IFinancialRule
from core.embeddings.embedding_service import EmbeddingService
from core.logger import get_logger

logger = get_logger("SemanticAnomalyRule")


class SemanticAnomalyRule(IFinancialRule):
    """
    Regra: Detecta se o conteúdo semântico de uma transação não condiz com sua categoria.
    Ex: "Compra de Pneus" na categoria "Alimentação".
    """

    def __init__(self, threshold_similarity: float = 0.3, lookback_n: int = 10):
        """
        Args:
            threshold_similarity: Se a similaridade for menor que isso, é anomalia.
            lookback_n: Quantas últimas transações analisar.
        """
        self.threshold = threshold_similarity
        self.lookback_n = lookback_n
        self._embedding_service = EmbeddingService()

    @property
    def rule_name(self) -> str:
        return "semantic_anomaly"

    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame,
        user_profile: dict[str, Any],
    ) -> RuleResult:
        if transactions_df.empty:
            return RuleResult(triggered=False)

        # Pega as últimas N transações de despesa
        last_txs = transactions_df[
            transactions_df[config.ColunasTransacoes.TIPO] == config.ValoresTipo.DESPESA
        ].tail(self.lookback_n)

        if last_txs.empty:
            return RuleResult(triggered=False)

        anomalies = []

        for _, row in last_txs.iterrows():
            desc = str(row[config.ColunasTransacoes.DESCRICAO])
            cat_name = str(row[config.ColunasTransacoes.CATEGORIA])

            if not desc or not cat_name or cat_name in ["Outros", "Desconhecido"]:
                continue

            # Gera embeddings
            desc_vec = self._embedding_service.get_embedding(desc)
            cat_vec = self._embedding_service.get_embedding(cat_name)

            if not desc_vec or not cat_vec:
                continue

            # Calcula similaridade
            sim = self._embedding_service.cosine_similarity(desc_vec, cat_vec)

            if sim < self.threshold:
                logger.info(
                    f"Anomalia detectada: '{desc}' em '{cat_name}' (Sim: {sim:.4f})"
                )
                anomalies.append(
                    f"- **{desc}** na categoria **{cat_name}** (Baixa coerência)"
                )

        if anomalies:
            msg = "🤔 **Gasto Estranho Detectado**\n\n"
            msg += "Encontrei alguns gastos que parecem estar na categoria errada:\n"
            msg += "\n".join(anomalies)
            msg += "\n\n*Dica: Você pode pedir para eu 'faxinar as transações' para organizar tudo.*"

            return RuleResult(
                triggered=True,
                message_template=msg,
                priority=NotificationPriority.MEDIUM,
                category="insight_anomaly",
            )

        return RuleResult(triggered=False)
