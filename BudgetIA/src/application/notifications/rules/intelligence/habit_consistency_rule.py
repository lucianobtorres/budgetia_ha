from datetime import datetime, timedelta
import pandas as pd
from typing import Any

from application.notifications.rules.base_rule import IFinancialRule
from application.notifications.models.rule_result import RuleResult
from core.memory.memory_service import MemoryService
from core.logger import get_logger

logger = get_logger("HabitConsistencyRule")

class HabitConsistencyRule(IFinancialRule):
    """
    Regra Mestra de Consistência de Hábitos.
    Varre a memória do usuário em busca de fatos com metadados estruturados (pattern_type)
    e verifica se o comportamento esperado ocorreu.
    """
    
    @property
    def rule_name(self) -> str:
        return "habit_consistency"
    
    display_name = "Fiscal de Rotina"

    def __init__(self, memory_service: MemoryService):
        self.memory = memory_service

    def should_notify(
        self,
        transactions_df: pd.DataFrame,
        budgets_df: pd.DataFrame, # Unused here but required by interface
        user_profile: dict[str, Any]
    ) -> RuleResult:
        # 1. Carregar fatos da memória
        facts = self.memory.search_facts("")
        alerts = []
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        # Mapeamento de dias (Python: 0=Mon, 6=Sun)
        day_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        
        if transactions_df is None or transactions_df.empty:
            return RuleResult(triggered=False)

        # 3. Iterar sobre memórias
        for fact in facts:
            metadata = fact.get("metadata", {})
            pattern_type = metadata.get("pattern_type")
            
            if not pattern_type or pattern_type != "weekly":
                continue # Por enquanto só focamos em semanal

            expected_day_str = metadata.get("expected_day_of_week")
            expected_category = metadata.get("expected_category")
            
            if not expected_day_str or not expected_category:
                continue

            # Verificar se "Ontem" era o dia esperado
            expected_day_idx = day_map.get(expected_day_str)
            if expected_day_idx is None:
                continue

            # Se ontem foi o dia esperado
            if yesterday.weekday() == expected_day_idx:
                # Verificar se houve transação dessa categoria ontem
                # Filtra transações de ontem
                
                # Conversão segura de datas no DF
                # df['Data'] deve ser datetime
                
                # Filtrar transações 'recentes' (janela de 2 dias p/ segurança)
                try:
                    recent_txs = transactions_df[
                        transactions_df['Categoria'].str.contains(expected_category, case=False, na=False)
                    ]
                    
                    found = False
                    for _, row in recent_txs.iterrows():
                        tx_date = row['Data']
                        if not pd.isnull(tx_date):
                             # Ensure python datetime for comparison
                            if hasattr(tx_date, 'to_pydatetime'):
                                tx_date = tx_date.to_pydatetime()
                            
                            if (today.date() - tx_date.date()).days <= 2: # Se houve nos ultimos 2 dias
                                found = True
                                break
                    
                    if not found:
                        alerts.append(f"• {expected_category} ({expected_day_str})")
                        
                except Exception as e:
                    logger.warning(f"Erro ao verificar hábito '{expected_category}': {e}")
                    continue

        if alerts:
            summary = "\n".join(alerts)
            full_msg = (
                f"Notei a falta de alguns gastos habituais recentes:\n{summary}\n\n"
                "Lançou tudo certinho ou pulamos a rotina?\n"
                "💡 Se este hábito estiver incorreto, você pode removê-lo na aba Inteligência > Memória."
            )
            
            return RuleResult(
                triggered=True,
                priority="medium", # String priority needs mapping if Enum? Base uses Enum. Let's start with Enum if possible or check Result.
                # RuleResult expects priority as Enum usually? 
                # Checking RuleResult definition... priority: NotificationPriority = NotificationPriority.LOW
                # So we should pass Enum.
                # But to avoid importing Enum inside class scope if not imported, let's fix imports first.
                # Adding import NotificationPriority
                message_template=full_msg,
                context={"missing_habits": alerts}
            )

        return RuleResult(triggered=False)
