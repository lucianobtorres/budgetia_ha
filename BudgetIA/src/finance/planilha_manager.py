# src/finance/planilha_manager.py
from __future__ import annotations
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from finance.repositories.budget_repository import BudgetRepository
    from finance.repositories.category_repository import CategoryRepository  # <--- Novo
    from finance.repositories.data_context import FinancialDataContext
    from finance.repositories.debt_repository import DebtRepository
    from finance.repositories.insight_repository import InsightRepository
    from finance.repositories.profile_repository import ProfileRepository
    from finance.repositories.transaction_repository import TransactionRepository
    from finance.services.category_service import CategoryService  # <--- Novo
    from finance.services.insight_service import InsightService
from core.logger import get_logger

logger = get_logger("PlanilhaManager")


class PlanilhaManager:
    """
    Orquestra os dados financeiros. (Fachada)
    Sua única responsabilidade é delegar chamadas para os repositórios e serviços.
    A construção e setup agora são feitos pela FinancialSystemFactory.
    """

    def __init__(
        self,
        context: "FinancialDataContext",
        transaction_repo: "TransactionRepository",
        budget_repo: "BudgetRepository",
        debt_repo: "DebtRepository",
        profile_repo: "ProfileRepository",
        insight_repo: "InsightRepository",
        category_repo: "CategoryRepository",  # <--- Novo
        category_service: "CategoryService",  # <--- Novo
        insight_service: "InsightService",
        cache_key: str,
    ) -> None:
        """
        Inicializa o gerenciador com as dependências já injetadas.
        """
        self._context = context
        self.transaction_repo = transaction_repo
        self.budget_repo = budget_repo
        self.debt_repo = debt_repo
        self.profile_repo = profile_repo
        self.insight_repo = insight_repo
        self.category_repo = category_repo  # <--- Novo
        self.category_service = category_service  # <--- Novo
        self.insight_service = insight_service
        self.cache_key = cache_key

        # Mantido para compatibilidade
        self.is_new_file = self._context.is_new_file

        # --- CONCURRENCY CONTROL ---
        from infrastructure.locking.lock_manager import RedisLockManager
        self.lock_manager = RedisLockManager(self._context.storage.resource_id)

    @property
    def lock_file(self):
        """Atalho para o context manager de lock."""
        return self.lock_manager.acquire

    def refresh_data(self) -> None:
        """
        Recarrega os dados do disco forçosamente para garantir 
        que estamos trabalhando com a versão mais recente antes de salvar.
        Útil para transações atômicas (Lock -> Refresh -> Update -> Save).
        """
        logger.debug("Recarregando dados do disco (Atomic Refresh)...")
        dfs, _ = self._context.storage.load_sheets(
            self._context.layout_config, self._context.strategy
        )
        self._context.data = dfs

    def save(self, add_intelligence: bool = False) -> None:
        self._context.save(add_intelligence)

    def visualizar_dados(self, aba_nome: str) -> pd.DataFrame:
        return self._context.get_dataframe(sheet_name=aba_nome) # type: ignore[no-any-return]

    def update_dataframe(self, sheet_name: str, new_df: pd.DataFrame) -> None:
        self._context.update_dataframe(sheet_name, new_df)

    def adicionar_registro(
        self,
        data: str,
        tipo: str,
        categoria: str,
        descricao: str,
        valor: float,
        status: str = "Concluído",
        parcelas: int = 1, # NEW Argument
    ) -> None:
        """
        Adiciona uma transação.
        A lógica de parcelamento (explosão em múltiplas transações) 
        agora reside no TransactionRepository.
        """
        self.transaction_repo.add_transaction(
            data, tipo, categoria, descricao, valor, status, parcelas
        )
        self.recalculate_budgets() # Memória
        self.save() # Single Commit

    def adicionar_registros_lote(
        self,
        transacoes: list[dict[str, Any]]
    ) -> int:
        """
        Adiciona múltiplas transações de uma vez.
        """
        count = self.transaction_repo.add_batch(transacoes)
        if count > 0:
            self.recalculate_budgets()
            self.save()
        return count


    def recalculate_budgets(self) -> None:
        self.budget_repo.recalculate_all_budgets()

    def delete_transaction(self, transaction_id: int) -> bool:
        success = self.transaction_repo.delete_transaction(transaction_id)
        if success:
            self.recalculate_budgets()
            self.save() # Single Commit
        return success

    def update_transaction(self, transaction_id: int, dados: dict[str, Any]) -> bool:
        success = self.transaction_repo.update_transaction(transaction_id, dados)
        if success:
            self.recalculate_budgets()
            self.save() # Single Commit
        return success

    def get_summary(self) -> dict[str, float]:
        return self.transaction_repo.get_summary() # type: ignore[no-any-return]

    def get_expenses_by_category(self, top_n: int = 5) -> pd.Series:
        return self.transaction_repo.get_expenses_by_category(top_n) # type: ignore[no-any-return]

    def adicionar_ou_atualizar_orcamento(
        self,
        categoria: str,
        valor_limite: float,
        periodo: str = "Mensal",
        observacoes: str = "",
    ) -> str:
        mensagem = self.budget_repo.add_or_update_budget(
            categoria=categoria,
            valor_limite=valor_limite,
            periodo=periodo,
            observacoes=observacoes,
        )
        self.recalculate_budgets()
        self.save() # Single Commit
        return mensagem

    def delete_budget(self, budget_id: int) -> bool:
        success = self.budget_repo.delete_budget(budget_id)
        if success:
            self.recalculate_budgets()
            self.save()
        return success

    def update_budget(self, budget_id: int, dados: dict[str, Any]) -> bool:
        success = self.budget_repo.update_budget_by_id(budget_id, dados)
        if success:
            self.recalculate_budgets()
            self.save()
        return success



    def adicionar_ou_atualizar_divida(
        self,
        nome_divida: str,
        valor_original: float,
        taxa_juros_mensal: float,
        parcelas_totais: int,
        valor_parcela: float,
        parcelas_pagas: int = 0,
        data_proximo_pgto: str | None = None,
        observacoes: str = "",
    ) -> str:
        return self.debt_repo.add_or_update_debt( # type: ignore[no-any-return]
            nome_divida=nome_divida,
            valor_original=valor_original,
            taxa_juros_mensal=taxa_juros_mensal,
            parcelas_totais=parcelas_totais,
            valor_parcela=valor_parcela,
            parcelas_pagas=parcelas_pagas,
            data_proximo_pgto=data_proximo_pgto,
            observacoes=observacoes,
        )

    def adicionar_insight_ia(
        self,
        data_insight: str,
        tipo_insight: str,
        titulo_insight: str,
        detalhes_recomendacao: str,
        status: str = "Novo",
    ) -> None:
        self.insight_repo.add_insight(
            data_insight=data_insight,
            tipo_insight=tipo_insight,
            titulo_insight=titulo_insight,
            detalhes_recomendacao=detalhes_recomendacao,
            status=status,
        )

    def salvar_dado_perfil(self, campo: str, valor: Any) -> str:
        return self.profile_repo.save_profile_field(campo=campo, valor=valor) # type: ignore[no-any-return]

    def get_perfil_como_texto(self) -> str:
        return self.profile_repo.get_profile_as_text() # type: ignore[no-any-return]

    def ensure_profile_fields(self, fields: list[str]) -> bool:
        return self.profile_repo.ensure_fields(fields) # type: ignore[no-any-return]

    def analisar_para_insights_proativos(self) -> list[dict[str, Any]]:
        logger.info("Delegando análise proativa para o InsightService.")
        return self.insight_service.run_proactive_analysis_orchestration() # type: ignore[no-any-return]

    # --- NOVO: MÉTODOS DE CATEGORIAS ---
    def get_categories(self) -> pd.DataFrame:
        """Retorna todas as categorias cadastradas."""
        return self.category_repo.get_all()

    def add_category(self, nome: str, tipo: str, icone: str = "", tags: str = "") -> bool:
        """Adiciona uma nova categoria."""
        success = self.category_repo.add_category(nome, tipo, icone, tags)
        if success:
            self.save()
        return success

    def delete_category(self, name: str) -> bool:
        """Remove uma categoria se não estiver em uso."""
        # 1. Check Use
        usage_count = self.transaction_repo.count_category_usage(name)
        if usage_count > 0:
            msg = f"Não é possível excluir '{name}': ela é usada em {usage_count} transações. Edite as transações ou renomeie a categoria."
            logger.warning(msg)
            # Retornar False aqui faria o endpoint retornar 404, o que é semânticamente errado mas ok-ish. 
            # Idealmente lançaríamos uma exceção específica, mas vamos logar e retornar False, 
            # e o Router pode tratar melhor se quiséssemos. 
            # BETTER: Raise ValueError to be caught by Router or let boolean fail.
            # Vamos levantar exception para mensagem customizada chegar na API
            raise ValueError(msg)

        success = self.category_repo.delete_category(name)
        if success:
            self.save()
        return success

    def update_category(self, old_name: str, new_name: str, tipo: str, icone: str, tags: str) -> bool:
        """Atualiza uma categoria existente."""
        success = self.category_repo.update_category(old_name, new_name, tipo, icone, tags)
        if success:
            # Se o nome mudou, atualiza em cascata nas transações
            if old_name.strip().lower() != new_name.strip().lower():
                self.transaction_repo.update_category_name(old_name, new_name)
            
            self.save()
        return success

    def ensure_default_categories(self) -> None:
        """Garante que existam categorias básicas (migração automática)."""
        pre_empty = self.category_repo.get_all().empty
        self.category_service.ensure_default_categories()
        # Salva apenas se houve alteração (estava vazia antes)
        if pre_empty and not self.category_repo.get_all().empty:
            self.save()  

    def check_connection(self) -> tuple[bool, str]:
        logger.debug("Verificando saúde da conexão com o armazenamento...")
        return self._context.storage.ping() # type: ignore[no-any-return]

    def clear_cache(self) -> None:
        logger.debug(
            f"Forçando invalidação de cache para '{self.cache_key}'"
        )
        self._context.cache.delete(self.cache_key)
