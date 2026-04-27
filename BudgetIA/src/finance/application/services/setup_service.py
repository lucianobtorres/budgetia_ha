# src/finance/services/setup_service.py
from typing import TYPE_CHECKING

from config import (
    DADOS_EXEMPLO_PATH,
    PROFILE_ESSENTIAL_FIELDS,
    ColunasOrcamentos,
    ColunasTransacoes,
    NomesAbas,
)
from core.logger import get_logger
from finance.utils import _carregar_dados_exemplo

logger = get_logger("SetupService")

if TYPE_CHECKING:
    from finance.domain.repositories.budget_repository import IBudgetRepository
    from finance.domain.repositories.data_context import FinancialDataContext
    from finance.domain.repositories.profile_repository import IProfileRepository
    from finance.domain.repositories.transaction_repository import (
        ITransactionRepository,
    )


class FinancialSetupService:
    """
    Serviço responsável por configurar a planilha inicial com dados de exemplo
    e garantir a estrutura básica necessária.
    """

    def __init__(
        self,
        context: "FinancialDataContext",
        transaction_repo: "ITransactionRepository",
        budget_repo: "IBudgetRepository",
        profile_repo: "IProfileRepository",
    ) -> None:
        self._context = context
        self._transaction_repo = transaction_repo
        self._budget_repo = budget_repo
        self._profile_repo = profile_repo

    def populate_initial_data(self) -> None:
        """Popula a planilha com dados de exemplo se estiver vazia."""
        logger.debug("Populando com dados de exemplo...")

        # 1. Orçamentos Iniciais
        if self._context.get_dataframe(NomesAbas.ORCAMENTOS).empty:
            self._populate_budgets()

        # 2. Transações Iniciais
        if self._context.get_dataframe(NomesAbas.TRANSACOES).empty:
            self._populate_transactions()
            # Recalcula orçamentos após adicionar transações
            self._budget_repo.recalculate_all_budgets()

        # 3. Campos de Perfil
        logger.debug("Garantindo campos de perfil...")
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
        from finance.domain.models.budget import Budget

        for o in orcamentos_dicts:
            budget = Budget(
                categoria=str(o[ColunasOrcamentos.CATEGORIA]),
                limite=float(str(o[ColunasOrcamentos.LIMITE])),
                periodo=str(o[ColunasOrcamentos.PERIODO]),
                observacoes=str(o.get(ColunasOrcamentos.OBS, "")),
            )
            self._budget_repo.save(budget)

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

        from finance.domain.models.transaction import Transaction

        for t in transacoes_exemplo:
            # Tenta pegar usando a chave do Config, ou chaves simples como fallback
            data_val = t.get(ColunasTransacoes.DATA, t.get("Data", "2024-01-01"))
            tipo_val = t.get(ColunasTransacoes.TIPO, t.get("Tipo", "Despesa"))
            cat_val = t.get(ColunasTransacoes.CATEGORIA, t.get("Categoria", "Outros"))
            desc_val = t.get(ColunasTransacoes.DESCRICAO, t.get("Descricao", ""))
            valor_val = t.get(ColunasTransacoes.VALOR, t.get("Valor", 0.0))
            status_val = t.get(ColunasTransacoes.STATUS, t.get("Status", "Concluído"))

            from datetime import datetime

            dt = datetime.strptime(str(data_val), "%Y-%m-%d").date()

            tx = Transaction(
                data=dt,
                tipo=str(tipo_val),
                categoria=str(cat_val),
                descricao=str(desc_val),
                valor=float(valor_val),
                status=str(status_val),
            )
            self._transaction_repo.save(tx)
