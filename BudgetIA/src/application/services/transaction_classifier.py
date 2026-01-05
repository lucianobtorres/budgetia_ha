import json
from datetime import datetime
import pandas as pd
from core.llm_manager import LLMOrchestrator
from core.logger import get_logger

logger = get_logger("TransactionClassifier")

class TransactionClassifier:
    """
    Serviço responsável por inferir categorias para transações não classificadas
    ou categorizadas como 'Outros'.
    """

    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.llm = llm_orchestrator

    def classify_transactions(self, transactions: list[dict], valid_categories: list[str]) -> dict[str, str]:
        """
        Recebe uma lista de transações e retorna um dicionário {id_transacao: nova_categoria}.
        Apenas retorna transações onde a confiança é alta.
        """
        if not transactions:
            return {}

        # Prepara o prompt
        tx_list_str = "\n".join([
            f"- ID: {t.get('id', 'N/A')} | Desc: {t.get('descricao', 'N/A')} | Valor: {t.get('valor', 'N/A')}" 
            for t in transactions
        ])
        
        valid_cats_str = ", ".join(valid_categories)

        prompt = f"""
        Você é um Assistente Contábil Especialista em Categorização de Despesas.
        Sua tarefa é analisar transações e atribuir a categoria CORRETA a partir de uma lista permitida.

        CATEGORIAS VÁLIDAS:
        [{valid_cats_str}]

        REGRAS:
        1. Use APENAS as categorias da lista acima. Se não encaixar, ignore.
        2. Se a descrição for vaga (ex: "Pix", "Compra"), NÃO categorize.
        3. Se for óbvio (ex: "Uber", "99Pop" -> Transporte), categorize.
        4. Retorne APENAS JSON válido.

        TRANSAÇÕES PARA ANALISAR:
        {tx_list_str}

        FORMATO DE SAÍDA (JSON):
        {{
            "classifications": [
                {{ "id": "ID_DA_TRANSACAO", "category": "CATEGORIA_ESCOLHIDA", "confidence": "high|medium|low" }}
            ]
        }}
        """

        try:
            # Chama LLM
            response = self.llm.get_configured_llm().invoke(prompt).content
            
            # Limpa markdown se houver
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            # Filtra resultados
            result = {}
            for item in data.get("classifications", []):
                if item.get("confidence") == "high" and item.get("category") in valid_categories:
                    # Garante que o ID existe na lista original
                    result[str(item["id"])] = item["category"]
            
            logger.info(f"Classificadas {len(result)} de {len(transactions)} transações com alta confiança.")
            return result

        except Exception as e:
            logger.error(f"Erro na classificação automática: {e}")
            return {}
