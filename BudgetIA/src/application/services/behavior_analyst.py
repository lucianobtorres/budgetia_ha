
import json
import pandas as pd
from datetime import datetime

from core.llm_manager import LLMOrchestrator
from core.memory.memory_service import MemoryService
from core.logger import get_logger
from langchain.schema import SystemMessage, HumanMessage

logger = get_logger("BehaviorAnalyst")


class BehaviorAnalyst:
    """
    Serviço "Observador" que analisa o histórico de transações para extrair
    padrões comportamentais e salvá-los na Memória de Longo Prazo.
    """

    def __init__(self, llm_orchestrator: LLMOrchestrator, memory_service: MemoryService):
        self.llm = llm_orchestrator.get_configured_llm()
        self.memory = memory_service

    def analyze_recent_transactions(self, transactions_df: pd.DataFrame, days: int = 60) -> list[str]:
        """
        Analisa transações recentes e gera fatos para a memória.
        
        Args:
            transactions_df: DataFrame com histórico.
            days: Janela de análise em dias.
            
        Returns:
            Lista de novos fatos aprendidos.
        """
        if transactions_df.empty:
            return []

        # Preparar dados para o LLM (resumo eficiente de tokens)
        # 1. Filtro de data
        # Assumindo coluna 'Data'
        # ... (simplificação para o MVP: pegar últimas 50 transações)
        recent_df = transactions_df.tail(50).copy()
        
        csv_data = recent_df.to_csv(index=False)

        prompt = f"""
        Você é um Analista Financeiro Comportamental.
        Analise o histórico de transações e identifique PADRÕES RECORRENTES de comportamento.
        
        Procure por:
        1. Gastos Semanais (Ex: Mercado todo Sábado, Uber para trabalho)
        2. Gastos Mensais (Ex: Assinaturas não detectadas anteriormente, Mensalidades)
        3. Hábitos de Valor (Ex: Gasta média de R$ 50 em lanches)

        DADOS (CSV):
        {csv_data}
        
        Saída OBRIGATÓRIA em JSON:
        Retorne uma lista de objetos com a seguinte estrutura:
        {{
            "facts": [
                {{
                    "description": "Texto legível do fato (Ex: 'Faz compra de mercado todo Sábado')",
                    "category": "Comportamento",
                    "metadata": {{
                        "pattern_type": "weekly" | "monthly" | "sporadic",
                        "expected_category": "Mercado" (ou categoria inferida),
                        "expected_day_of_week": "Saturday" (se semanal),
                        "expected_day_of_month": 15 (se mensal),
                        "avg_amount": 500.0,
                        "confidence": 0.0 to 1.0
                    }}
                }}
            ]
        }}
        """

        try:
            messages = [
                SystemMessage(content="Você é um componente de backend que analisa dados financeiros e retorna JSON estruturado."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            content = response.content.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(content)
            facts_data = result.get("facts", [])
            
            learned_facts = []
            for item in facts_data:
                description = item.get("description")
                category = item.get("category", "Comportamento")
                meta = item.get("metadata", {})
                
                if description:
                    self.memory.add_fact(category, description, source="behavior_analyst", metadata=meta)
                    learned_facts.append(description)
                
            return learned_facts

        except Exception as e:
            logger.error(f"Falha na análise LLM: {e}")
            return []
