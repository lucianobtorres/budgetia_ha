from core.logger import get_logger
from ofxparse import OfxParser
from typing import BinaryIO
from pydantic import BaseModel
from datetime import datetime
from core.llm_manager import LLMOrchestrator
from finance.repositories.category_repository import CategoryRepository
from langchain_core.messages import SystemMessage, HumanMessage
import json

logger = get_logger("ImportService")

class ImportedTransaction(BaseModel):
    data: str
    descricao: str
    valor: float
    tipo: str # Receita ou Despesa
    categoria: str
    reference_id: str | None = None

from finance.repositories.transaction_repository import TransactionRepository

class ImportService:
    def __init__(self, llm_orchestrator: LLMOrchestrator, category_repo: CategoryRepository, transaction_repo: TransactionRepository):
        self.llm_orchestrator = llm_orchestrator
        self.category_repo = category_repo
        self.transaction_repo = transaction_repo

    def parse_ofx(self, file: BinaryIO) -> list[ImportedTransaction]:
        try:
            ofx = OfxParser.parse(file)
        except Exception as e:
            logger.error(f"Erro ao parsear OFX com ofxparse: {e}")
            raise ValueError("Arquivo OFX inválido ou corrompido.")
        
        transactions = []
        descriptions_to_classify = []
        
        # Build deduplication set from existing DB
        existing_df = self.transaction_repo.get_all_transactions()
        existing_signatures = set()
        
        from config import ColunasTransacoes
        if not existing_df.empty and ColunasTransacoes.DATA in existing_df.columns:
            # Create signature: (DataStr, ValorFloat, DescricaoStr)
            # Use same normalization as parsing
            for _, row in existing_df.iterrows():
                try:
                    d_str = row[ColunasTransacoes.DATA].strftime('%Y-%m-%d')
                    val = float(row[ColunasTransacoes.VALOR])
                    desc = str(row[ColunasTransacoes.DESCRICAO]).strip().lower() # Lowercase for signature
                    existing_signatures.add((d_str, val, desc))
                except:
                    continue
        
        # 1. Parse Raw Data
        for account in ofx.accounts:
            for t in account.statement.transactions:
                tipo = "Receita" if t.amount > 0 else "Despesa"
                descricao = t.payee if t.payee else t.memo
                descricao = descricao.strip() if descricao else "Sem Descrição"
                
                # Normalização da data (YYYY-MM-DD)
                data_str = t.date.strftime('%Y-%m-%d')
                
                # Normalização do valor (sempre positivo para exibição, tipo define sinal)
                valor = abs(float(t.amount))
                
                # Check duplication (Case Insensitive)
                if (data_str, valor, descricao.lower()) in existing_signatures:
                    continue # SKIP DUPLICATE
                
                # Format Description to Title Case for better UI
                formatted_desc = descricao.title()

                transactions.append(ImportedTransaction(
                    data=data_str,
                    descricao=formatted_desc,
                    valor=valor,
                    tipo=tipo,
                    categoria="Outros",
                    reference_id=t.id,
                    is_duplicate=False
                ))
                descriptions_to_classify.append(formatted_desc)
        
        logger.info(f"OFX: {len(transactions)} novas transações encontradas (após deduplicação).")

        # 2. Auto-Classify (Batch)
        if not transactions:
            return []

        try:
            mapping = self.classify_batch(list(set(descriptions_to_classify)))
            logger.info(f"Mapping obtido: {mapping}")
            
            classified_count = 0
            for tx in transactions:
                if tx.descricao in mapping:
                    mapped_cat = mapping[tx.descricao]
                    # Validate if category exists, otherwise fallback? 
                    # LLM instructed to verify, but let's trust it for now or it defaults to existing string
                    if mapped_cat and mapped_cat != "Outros" and mapped_cat != "A Classificar":
                        tx.categoria = mapped_cat
                        classified_count += 1
            logger.info(f"Auto-classificação aplicada em {classified_count} transações.")
            
        except Exception as e:
            logger.error(f"Erro CRÍTICO na auto-classificação: {e}", exc_info=True)
            
        return transactions

    def classify_batch(self, descriptions: list[str]) -> dict[str, str]:
        if not descriptions:
            return {}

        categories = self.category_repo.get_all_category_names()
        if "Outros" not in categories:
            categories.append("Outros")
        
        logger.debug(f"Categorias disponíveis: {categories}")
        logger.debug(f"Descrições para classificar: {descriptions}")

        # Sugestões de categorias padrão para enriquecer o contexto se a lista do usuário for pobre
        sugestoes_padrao = [
            "Alimentação", "Transporte", "Moradia", "Educação", "Saúde", "Lazer", 
            "Investimentos", "Receitas", "Tarifas Bancárias", "Transferências", 
            "Compras", "Assinaturas", "Serviços"
        ]

        prompt = f"""
Você é um especialista experiente em finanças pessoais.
Sua missão é mapear as DESCRIÇÕES de transações abaixo para a MELHOR CATEGORIA possível.

LISTA DE CATEGORIAS JÁ EXISTENTES DO USUÁRIO:
{json.dumps(categories, ensure_ascii=False)}

SUGESTÕES DE CATEGORIAS PADRÃO (Use se necessário):
{json.dumps(sugestoes_padrao, ensure_ascii=False)}

DESCRIÇÕES PARA CLASSIFICAR:
{json.dumps(descriptions, ensure_ascii=False)}

REGRAS CRITICAS:
1. EVITE AO MÁXIMO usar "Outros", "A Classificar" ou "Geral". Seja específico.
2. Se a categoria atual ("A Classificar" ou "Outros") for ruim, MUDE para uma das sugestões acima.
3. Se a descrição for vaga (ex: "Pix Enviado"), tente inferir "Transferências" ou "Serviços" se não houver contexto melhor.
4. Para lojas conhecidas (ex: "Magazine Luiza", "Amazon"), use "Compras" ou a categoria específica do item se óbvio.
5. Para rendimentos (ex: "Juros", "Dividendos", "Resgate"), use "Investimentos" ou "Receitas".
6. Para taxas de banco, use "Tarifas Bancárias".
7. Retorne APENAS um JSON válido no formato: {{"descricao": "categoria_escolhida"}} (Use exatamente a string da descrição dada).
"""
        try:
            llm = self.llm_orchestrator.get_current_llm()
            response = llm.invoke([
                SystemMessage(content="Você é um classificador JSON estrito. Responda APENAS JSON."),
                HumanMessage(content=prompt)
            ])
            
            content = response.content
            logger.debug(f"LLM Raw Response: {content}")
            
            # Limpeza
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            raw_mapping = json.loads(content.strip())
            
            # Normalizar para Dict se vier lista
            final_mapping = {}
            if isinstance(raw_mapping, list):
                for item in raw_mapping:
                    if isinstance(item, dict) and "descricao" in item and "categoria" in item:
                        final_mapping[item["descricao"]] = item["categoria"]
            elif isinstance(raw_mapping, dict):
                 # Check format: simple dict {desc: cat} or complex
                 # Prompt asked for {"descricao": "cat"} which implies structure per item if list, 
                 # OR maybe {"Netlfis": "Streaming"}?
                 # Given the log, it returned a list. But let's handle simple dict too.
                 final_mapping = raw_mapping

            return final_mapping
        except json.JSONDecodeError as je:
             logger.error(f"Erro ao decodificar JSON do LLM: {je}. Content: {content}")
             return {}
        except Exception as e:
            logger.error(f"LLM Classification Failed: {e}", exc_info=True)
            return {}
