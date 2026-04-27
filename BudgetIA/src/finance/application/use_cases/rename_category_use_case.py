from datetime import datetime

from finance.domain.services.budget_service import BudgetDomainService
from finance.domain.services.category_service import CategoryDomainService
from finance.domain.services.transaction_service import TransactionDomainService


class RenameCategoryUseCase:
    """
    Caso de Uso: Renomear uma categoria com efeito cascata em transações e orçamentos.
    """

    def __init__(
        self,
        category_service: CategoryDomainService,
        transaction_service: TransactionDomainService,
        budget_service: BudgetDomainService,
    ):
        self._category_service = category_service
        self._transaction_service = transaction_service
        self._budget_service = budget_service

    def execute(self, old_name: str, new_name: str) -> bool:
        # 1. Renomeia a categoria no repositório de categorias
        success = self._category_service.rename_category(old_name, new_name)
        if not success:
            return False

        # 2. Atualiza todas as transações que usavam o nome antigo (Cascata)
        self._transaction_service.update_category_names(old_name, new_name)

        # 3. Recalcula orçamentos para o mês atual para refletir a mudança
        # (Idealmente recalcularíamos todos os meses afetados, mas seguiremos o padrão atual)
        now = datetime.now()
        self._budget_service.recalculate_budgets(now.month, now.year)

        return True
