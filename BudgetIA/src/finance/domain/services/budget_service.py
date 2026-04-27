from datetime import date

from ..models.budget import Budget
from ..repositories.budget_repository import IBudgetRepository
from ..repositories.transaction_repository import ITransactionRepository


class BudgetDomainService:
    """
    Serviço de Domínio para Orçamentos.
    Orquestra a lógica de recálculo baseada em transações.
    """

    def __init__(
        self,
        budget_repository: IBudgetRepository,
        transaction_repository: ITransactionRepository,
    ):
        self._budget_repo = budget_repository
        self._transaction_repo = transaction_repository

    def recalculate_budgets(
        self, month: int | None = None, year: int | None = None
    ) -> int:
        """
        Recalcula o valor gasto de todos os orçamentos para o período informado.
        Se mês/ano não forem informados, usa o mês atual.
        """
        if month is None or year is None:
            today = date.today()
            month = month or today.month
            year = year or today.year

        # 1. Busca todos os orçamentos cadastrados
        budgets = self._budget_repo.list_all()
        if not budgets:
            return 0

        # 2. Busca todas as transações do período
        transactions = self._transaction_repo.list_all(month=month, year=year)

        # Filtra apenas despesas
        expenses = [tx for tx in transactions if tx.eh_despesa]

        # 3. Mapeia total gasto por categoria
        spending_by_category = {}
        for tx in expenses:
            cat = tx.categoria
            spending_by_category[cat] = spending_by_category.get(cat, 0.0) + tx.valor

        # 4. Atualiza cada orçamento
        updated_count = 0
        for budget in budgets:
            new_spending = spending_by_category.get(budget.categoria, 0.0)

            # Só atualiza se o valor mudou (otimização)
            if budget.gasto_atual != new_spending:
                budget.gasto_atual = new_spending
                self._budget_repo.save(budget)
                updated_count += 1

        return updated_count

    def add_or_update_budget(
        self,
        categoria: str,
        valor_limite: float,
        periodo: str = "Mensal",
        observacoes: str | None = None,
    ) -> Budget:
        """
        Lógica de domínio para garantir que só exista um orçamento por categoria.
        """
        existing = self._budget_repo.get_by_category(categoria)

        if existing:
            existing.limite = valor_limite
            existing.periodo = periodo
            existing.observacoes = observacoes
            return self._budget_repo.save(existing)
        else:
            new_budget = Budget(
                categoria=categoria,
                limite=valor_limite,
                periodo=periodo,
                observacoes=observacoes,
            )
            return self._budget_repo.save(new_budget)
