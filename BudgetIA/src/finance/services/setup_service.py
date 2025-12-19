# src/finance/services/setup_service.py
from typing import TYPE_CHECKING

from config import (
    DADOS_EXEMPLO_PATH,
    PROFILE_ESSENTIAL_FIELDS,
    ColunasOrcamentos,
    ColunasTransacoes,
    NomesAbas,
)
from finance.utils import _carregar_dados_exemplo

if TYPE_CHECKING:
    from finance.repositories.budget_repository import BudgetRepository
    from finance.repositories.data_context import FinancialDataContext
    from finance.repositories.profile_repository import ProfileRepository
    from finance.repositories.transaction_repository import TransactionRepository


class FinancialSetupService:
    """
    Serviço responsável por configurar a planilha inicial com dados de exemplo
    e garantir a estrutura básica necessária.
    """

    def __init__(
        self,
        context: "FinancialDataContext",
        transaction_repo: "TransactionRepository",
        budget_repo: "BudgetRepository",
        profile_repo: "ProfileRepository",
    ) -> None:
        self._context = context
        self._transaction_repo = transaction_repo
        self._budget_repo = budget_repo
        self._profile_repo = profile_repo

    def populate_initial_data(self) -> None:
        """Popula a planilha com dados de exemplo se estiver vazia."""
        print("--- DEBUG SetupService: Populando com dados de exemplo... ---")

        # 1. Orçamentos Iniciais
        if self._context.get_dataframe(NomesAbas.ORCAMENTOS).empty:
            self._populate_budgets()

        # 2. Transações Iniciais
        if self._context.get_dataframe(NomesAbas.TRANSACOES).empty:
            self._populate_transactions()
            # Recalcula orçamentos após adicionar transações
            self._budget_repo.recalculate_all_budgets()

        # 3. Campos de Perfil
        print("--- DEBUG SetupService: Garantindo campos de perfil... ---")
        self._profile_repo.ensure_fields(PROFILE_ESSENTIAL_FIELDS)

        # Salva tudo no final
        self._context.save(add_intelligence=True)

    def _populate_budgets(self) -> None:
        orcamentos_dicts = [
            {
                ColunasOrcamentos.CATEGORIA: "Alimentação",
                ColunasOrcamentos.LIMITE: 600.0,
                ColunasOrcamentos.PERIODO: "Mensal",
                ColunasOrcamentos.OBS: "",
            },
            {
                ColunasOrcamentos.CATEGORIA: "Transporte",
                ColunasOrcamentos.LIMITE: 250.0,
                ColunasOrcamentos.PERIODO: "Mensal",
                ColunasOrcamentos.OBS: "",
            },
        ]
        for o in orcamentos_dicts:
            self._budget_repo.add_or_update_budget(
                categoria=str(o[ColunasOrcamentos.CATEGORIA]),
                valor_limite=float(o[ColunasOrcamentos.LIMITE]),
                periodo=str(o[ColunasOrcamentos.PERIODO]),
                observacoes=str(o.get(ColunasOrcamentos.OBS, "")),
            )

    def _populate_transactions(self) -> None:
        transacoes_exemplo = _carregar_dados_exemplo(DADOS_EXEMPLO_PATH)
        if not transacoes_exemplo:
            transacoes_exemplo = [
                {
                    ColunasTransacoes.DATA: "2024-07-01",
                    ColunasTransacoes.TIPO: "Receita",
                    ColunasTransacoes.CATEGORIA: "Salário",
                    ColunasTransacoes.DESCRICAO: "Pagamento",
                    ColunasTransacoes.VALOR: 5000.0,
                    ColunasTransacoes.STATUS: "Concluído",
                },
                {
                    ColunasTransacoes.DATA: "2024-07-05",
                    ColunasTransacoes.TIPO: "Despesa",
                    ColunasTransacoes.CATEGORIA: "Moradia",
                    ColunasTransacoes.DESCRICAO: "Aluguel",
                    ColunasTransacoes.VALOR: 1500.0,
                    ColunasTransacoes.STATUS: "Concluído",
                },
            ]

        for t in transacoes_exemplo:
            self._transaction_repo.add_transaction(
                data=str(t.get(ColunasTransacoes.DATA, t.get("Data", "2024-01-01"))),
                tipo=str(t[ColunasTransacoes.TIPO]),
                categoria=str(t[ColunasTransacoes.CATEGORIA]),
                descricao=str(t.get(ColunasTransacoes.DESCRICAO, "")),
                valor=float(t[ColunasTransacoes.VALOR]),
                status=str(t.get(ColunasTransacoes.STATUS, "Concluído")),
            )
