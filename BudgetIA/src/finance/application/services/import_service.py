import json
from typing import BinaryIO

from langchain_core.messages import HumanMessage, SystemMessage
from ofxparse import OfxParser
from pydantic import BaseModel

from core.llm_manager import LLMOrchestrator
from core.logger import get_logger

from ...domain.repositories.category_repository import ICategoryRepository
from ...domain.repositories.transaction_repository import ITransactionRepository

logger = get_logger("ImportService")


class ImportedTransaction(BaseModel):
    data: str
    descricao: str
    valor: float
    tipo: str  # Receita ou Despesa
    categoria: str
    reference_id: str | None = None
    is_duplicate: bool = False


class ImportService:
    def __init__(
        self,
        llm_orchestrator: LLMOrchestrator,
        category_repo: ICategoryRepository,
        transaction_repo: ITransactionRepository,
    ):
        self.llm_orchestrator = llm_orchestrator
        self.category_repo = category_repo
        self.transaction_repo = transaction_repo

    def parse_ofx(self, file: BinaryIO) -> list[ImportedTransaction]:
        try:
            ofx = OfxParser.parse(file)
        except Exception as e:
            logger.error(f"Erro ao parsear OFX com ofxparse: {e}")
            raise ValueError("Arquivo OFX inválido ou corrompido.")

        transactions: list[ImportedTransaction] = []
        descriptions_to_classify = []

        # Build deduplication set from existing transactions
        existing_txs = self.transaction_repo.list_all()
        existing_signatures = set()

        for tx in existing_txs:
            try:
                d_str = tx.data.strftime("%Y-%m-%d")
                val = float(tx.valor)
                desc = tx.descricao.strip().lower()
                existing_signatures.add((d_str, val, desc))
            except Exception:
                continue

        # 1. Parse Raw Data
        for account in ofx.accounts:
            for t in account.statement.transactions:
                tipo = "Receita" if t.amount > 0 else "Despesa"
                descricao = t.payee if t.payee else t.memo
                descricao = descricao.strip() if descricao else "Sem Descrição"

                # Normalização da data (YYYY-MM-DD)
                data_str = t.date.strftime("%Y-%m-%d")

                # Normalização do valor (sempre positivo para exibição)
                valor = abs(float(t.amount))

                # Check duplication (Case Insensitive)
                if (data_str, valor, descricao.lower()) in existing_signatures:
                    continue

                # Format Description to Title Case for better UI
                formatted_desc = descricao.title()

                transactions.append(
                    ImportedTransaction(
                        data=data_str,
                        descricao=formatted_desc,
                        valor=valor,
                        tipo=tipo,
                        categoria="Outros",
                        reference_id=t.id,
                        is_duplicate=False,
                    )
                )
                descriptions_to_classify.append(formatted_desc)

        logger.info(f"OFX: {len(transactions)} novas transações encontradas.")

        # 2. Auto-Classify (Batch)
        if not transactions:
            return []

        try:
            mapping = self.classify_batch(list(set(descriptions_to_classify)))

            classified_count = 0
            for tx in transactions:
                if tx.descricao in mapping:
                    mapped_cat = mapping[tx.descricao]
                    if mapped_cat and mapped_cat not in ["Outros", "A Classificar"]:
                        tx.categoria = mapped_cat
                        classified_count += 1
            logger.info(
                f"Auto-classificação aplicada em {classified_count} transações."
            )

        except Exception as e:
            logger.error(f"Erro na auto-classificação: {e}")

        return transactions

    def classify_batch(self, descriptions: list[str]) -> dict[str, str]:
        if not descriptions:
            return {}

        categories = self.category_repo.get_all_category_names()
        if "Outros" not in categories:
            categories.append("Outros")

        # Coleta exemplos do histórico para Few-Shot Prompting
        history = self.transaction_repo.list_all()
        examples = {}
        for tx in reversed(history):
            if len(examples) >= 30:
                break
            desc_clean = tx.descricao.strip()
            if (
                tx.categoria
                and tx.categoria not in ["Outros", "A Classificar"]
                and desc_clean not in examples
            ):
                examples[desc_clean] = tx.categoria

        prompt = f"""
Você é um especialista em finanças. Mapeie as NOVAS DESCRIÇÕES abaixo para a MELHOR CATEGORIA.

CATEGORIAS PERMITIDAS:
{json.dumps(categories, ensure_ascii=False)}

EXEMPLOS DO HISTÓRICO DO USUÁRIO (Use como referência de estilo e preferência):
{json.dumps(examples, ensure_ascii=False)}

NOVAS DESCRIÇÕES PARA CATEGORIZAR:
{json.dumps(descriptions, ensure_ascii=False)}

REGRAS:
1. Seja específico. Evite "Outros" se houver uma categoria melhor.
2. Mantenha a consistência com o histórico do usuário.
3. Retorne APENAS um JSON plano: {{"descricao": "categoria"}}
"""
        try:
            llm = self.llm_orchestrator.get_current_llm()
            response = llm.invoke(
                [
                    SystemMessage(content="Responda APENAS JSON."),
                    HumanMessage(content=prompt),
                ]
            )

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"LLM Classification Failed: {e}")
            return {}
