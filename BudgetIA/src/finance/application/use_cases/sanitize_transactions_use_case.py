from typing import Any

from core.llm_manager import LLMOrchestrator
from core.logger import get_logger
from finance.application.services.import_service import ImportService
from finance.domain.repositories.category_repository import ICategoryRepository
from finance.domain.repositories.transaction_repository import ITransactionRepository
from finance.domain.services.transaction_service import TransactionDomainService

logger = get_logger("SanitizeTransactionsUseCase")


class SanitizeTransactionsUseCase:
    """
    Caso de Uso: Realiza a limpeza e re-classificação de transações classificadas como 'Outros' ou 'A Classificar'.
    """

    def __init__(
        self,
        llm_orchestrator: LLMOrchestrator,
        category_repo: ICategoryRepository,
        transaction_repo: ITransactionRepository,
        transaction_service: TransactionDomainService,
    ):
        self._llm_orchestrator = llm_orchestrator
        self._category_repo = category_repo
        self._transaction_repo = transaction_repo
        self._transaction_service = transaction_service

    def execute(self) -> dict[str, Any]:
        """
        Executa a faxina de dados usando IA para classificar transações obscuras.
        """
        logger.info("Iniciando faxina de dados (Sanitization)...")

        # 1. Buscar todas as transações
        transactions = self._transaction_repo.list_all()
        if not transactions:
            return {"status": "skipped", "reason": "No transactions found"}

        # 2. Filtrar transações alvo
        target_categories = ["Outros", "A Classificar", "nan", "None", ""]
        targets = [
            tx
            for tx in transactions
            if not tx.categoria or tx.categoria in target_categories
        ]

        if not targets:
            return {
                "status": "success",
                "processed": 0,
                "message": "Nenhuma transação para classificar.",
            }

        # 3. Extrair descrições únicas para classificação em lote
        descriptions = list(set(tx.descricao for tx in targets if tx.descricao))
        if not descriptions:
            return {"status": "success", "processed": 0}

        # 4. Usar o ImportService (que já tem a lógica de IA)
        # Nota: ImportService ainda não foi totalmente refatorado para DDD Interfaces,
        # mas como ele aceita repositórios, vamos passar os que temos.
        # TODO: Refatorar ImportService para aceitar Interfaces em vez de classes concretas.
        service = ImportService(
            self._llm_orchestrator, self._category_repo, self._transaction_repo
        )  # type: ignore[arg-type]

        mapping = service.classify_batch(descriptions)
        if not mapping:
            return {
                "status": "warning",
                "processed": 0,
                "message": "IA não retornou sugestões.",
            }

        normalized_map = {k.strip().lower(): v for k, v in mapping.items()}

        # 5. Aplicar atualizações
        changes_count = 0
        for tx in targets:
            original_desc = tx.descricao.strip()
            new_cat = mapping.get(original_desc) or normalized_map.get(
                original_desc.lower()
            )

            if new_cat and new_cat not in target_categories:
                tx.categoria = new_cat
                self._transaction_repo.save(tx)
                changes_count += 1
                logger.debug(f"Classificação Automática: {original_desc} -> {new_cat}")

        return {
            "status": "success",
            "processed": changes_count,
            "details": f"{changes_count} itens re-classificados com sucesso.",
        }
