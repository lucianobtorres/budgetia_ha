
import json
import pandas as pd
from datetime import datetime

from core.llm_manager import LLMOrchestrator
from core.memory.memory_service import MemoryService
from langchain.schema import SystemMessage, HumanMessage


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
        Você é um Analista Financeiro Comportamental (O Observador).
        Seu objetivo é analisar o histórico de transações cruas e deduzir FATOS sobre o comportamento do usuário.
        
        Regras para Fatos:
        1. Devem ser padrões recorrentes ou significativos (não fatos isolados triviais).
        2. Devem ter utilidade para planejamento futuro.
        3. Devem ser neutros e descritivos.
        
        Exemplos de Bons Fatos:
        - "Usuário gasta em média R$ 400 com Delivery nos fins de semana."
        - "Há uma assinatura recorrente de Streaming de R$ 50 no dia 15."
        - "Gastos de transporte aumentaram significativamente na última quinzena."
        
        Exemplos de Maus Fatos:
        - "Usuário comprou um café." (Trivial)
        - "Usuário gasta muito." (Vago)
        
        DADOS (CSV):
        {csv_data}
        
        Saída:
        Retorne APENAS um JSON com uma lista de strings.
        Ex: {{"facts": ["fato 1", "fato 2"]}}
        Se não encontrar nada relevante, retorne lista vazia.
        """

        try:
            messages = [
                SystemMessage(content="Você é um componente de backend que analisa dados financeiros."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            content = response.content.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(content)
            facts = result.get("facts", [])
            
            learned_facts = []
            for fact in facts:
                # Verificar se fato já existe na memória (busca semântica ou exata simplificada)
                # O ideal seria vector search, mas por enquanto vamos confiar na dedução do add_fact
                # que já evita duplicatas exatas, vamos adicionar source='observer'
                
                self.memory.add_fact("Comportamento", fact, source="observer")
                learned_facts.append(fact)
                
            return learned_facts

        except Exception as e:
            print(f"ERRO (BehaviorAnalyst): Falha na análise LLM: {e}")
            return []
