from datetime import datetime, timedelta
from typing import Any

import pandas as pd

import config
from application.notifications.models.notification_message import NotificationPriority
from application.notifications.models.rule_result import RuleResult
from application.notifications.rules.base_rule import IFinancialRule


class SubscriptionAuditorRule(IFinancialRule): # type: ignore[misc]
    """
    Regra de Auditoria: Caçador de Assinaturas.
    Monitora transações recentes buscando serviços de assinatura conhecidos
    (Netflix, Spotify, Amazon, Apple, Google, Disney, HBO, Smartfit, Gympass).
    
    Objetivo: Questionar a utilidade do gasto assim que ele ocorre.
    """

    def __init__(self, days_lookback: int = 3):
        self.days_lookback = days_lookback
        self.subscription_keywords = [
            "netflix", "spotify", "amazon prime", "prime video", 
            "disney", "hbo", "apple.com/bill", "google storage", 
            "youtube premium", "smartfit", "gympass", "sem par", "veloe"
        ]

    @property
    def rule_name(self) -> str:
        return "subscription_auditor"

    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame,
        user_profile: dict[str, Any],
    ) -> RuleResult:
        
        print(f"LOG (SubscriptionAuditor): Auditando assinaturas nos últimos {self.days_lookback} dias...")

        if transactions_df.empty:
            return RuleResult(triggered=False)

        # 1. Preparar DataFrame
        df = transactions_df.copy()
        if config.ColunasTransacoes.DATA not in df.columns:
            return RuleResult(triggered=False)
            
        df[config.ColunasTransacoes.DATA] = pd.to_datetime(df[config.ColunasTransacoes.DATA], errors='coerce')
        
        # 2. Filtrar data recente (Janela de Auditoria)
        cutoff_date = datetime.now() - timedelta(days=self.days_lookback)
        recent_tx = df[df[config.ColunasTransacoes.DATA] >= cutoff_date]
        
        if recent_tx.empty:
            return RuleResult(triggered=False)

        alerts = []

        # 3. Analisar cada transação recente
        for _, row in recent_tx.iterrows():
            descricao = str(row.get(config.ColunasTransacoes.DESCRICAO, "")).lower()
            valor = float(row.get(config.ColunasTransacoes.VALOR, 0.0))
            
            # Só audita despesas (valor negativo ou positivo dependendo do padrão, assumindo users registram valor absoluto)
            # Mas geralmente assinatura é saída. Assumindo que tudo no DF de transações é relevante.
            
            for keyword in self.subscription_keywords:
                if keyword in descricao:
                    valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    msg = (
                        f"🕵️‍♂️ **Auditoria de Assinaturas**\n"
                        f"Identifiquei um pagamento recente para *{keyword.title()}* ({valor_fmt}).\n"
                        f"Pergunta rápida: **Você usou este serviço este mês?**\n"
                        f"Se não, que tal cancelar e economizar esses {valor_fmt}?"
                    )
                    alerts.append(msg)
                    # Break keyword loop to avoid double match on same row
                    break
        
        if alerts:
            # Retorna o primeiro alerta encontrado (para não spammar 10 de uma vez)
            return RuleResult(
                triggered=True,
                message_template=alerts[0], # Envia um por vez
                priority=NotificationPriority.LOW, # Baixa, pois é educativo/auditoria
                category="audit_subscription"
            )

        return RuleResult(triggered=False)
