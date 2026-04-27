# src/finance/factory.py
import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from config import LAYOUT_PLANILHA
from core.embeddings.embedding_service import EmbeddingService
from core.logger import get_logger

if TYPE_CHECKING:
    from core.llm_manager import LLMOrchestrator
    from core.user_config_service import UserConfigService
    from finance.storage.base_storage_handler import BaseStorageHandler

# Importações de Casos de Uso e Repositórios
from finance.application.use_cases.add_insight_use_case import (
    AddInsightUseCase,  # noqa: E402
)
from finance.application.use_cases.add_or_update_debt_use_case import (
    AddOrUpdateDebtUseCase,
)  # noqa: E402
from finance.application.use_cases.add_or_update_goal_use_case import (
    AddOrUpdateGoalUseCase,
)  # noqa: E402
from finance.application.use_cases.add_transaction_use_case import (
    AddTransactionUseCase,  # noqa: E402
)
from finance.application.use_cases.define_budget_use_case import (
    DefineBudgetUseCase,  # noqa: E402
)
from finance.application.use_cases.delete_budget_use_case import (
    DeleteBudgetUseCase,  # noqa: E402
)
from finance.application.use_cases.delete_debt_use_case import (
    DeleteDebtUseCase,  # noqa: E402
)
from finance.application.use_cases.delete_goal_use_case import (
    DeleteGoalUseCase,  # noqa: E402
)
from finance.application.use_cases.delete_transaction_use_case import (
    DeleteTransactionUseCase,
)  # noqa: E402
from finance.application.use_cases.generate_proactive_insights_use_case import (
    GenerateProactiveInsightsUseCase,
)  # noqa: E402
from finance.application.use_cases.get_expenses_by_category_use_case import (
    GetExpensesByCategoryUseCase,
)  # noqa: E402
from finance.application.use_cases.get_profile import GetProfileUseCase  # noqa: E402
from finance.application.use_cases.get_summary_use_case import (
    GetSummaryUseCase,  # noqa: E402
)
from finance.application.use_cases.list_budgets_use_case import (
    ListBudgetsUseCase,  # noqa: E402
)
from finance.application.use_cases.list_debts_use_case import (
    ListDebtsUseCase,  # noqa: E402
)
from finance.application.use_cases.list_goals_use_case import (
    ListGoalsUseCase,  # noqa: E402
)
from finance.application.use_cases.list_transactions_use_case import (
    ListTransactionsUseCase,
)  # noqa: E402
from finance.application.use_cases.rename_category_use_case import (
    RenameCategoryUseCase,  # noqa: E402
)
from finance.application.use_cases.sanitize_transactions_use_case import (
    SanitizeTransactionsUseCase,
)  # noqa: E402
from finance.application.use_cases.update_budget_use_case import (
    UpdateBudgetUseCase,  # noqa: E402
)
from finance.application.use_cases.update_profile import (
    UpdateProfileUseCase,  # noqa: E402
)
from finance.application.use_cases.update_transaction_use_case import (
    UpdateTransactionUseCase,
)  # noqa: E402
from finance.domain.services.budget_service import BudgetDomainService  # noqa: E402
from finance.domain.services.category_service import CategoryDomainService  # noqa: E402
from finance.domain.services.semantic_category_service import (
    SemanticCategoryService,  # noqa: E402
)
from finance.domain.services.transaction_service import (
    TransactionDomainService,  # noqa: E402
)
from finance.infrastructure.persistence.data_context import (
    FinancialDataContext,  # noqa: E402
)
from finance.infrastructure.persistence.excel_budget_repository import (
    ExcelBudgetRepository,
)  # noqa: E402
from finance.infrastructure.persistence.excel_category_repository import (
    ExcelCategoryRepository,
)  # noqa: E402
from finance.infrastructure.persistence.excel_debt_repository import (
    ExcelDebtRepository,  # noqa: E402
)
from finance.infrastructure.persistence.excel_goal_repository import (
    ExcelGoalRepository,  # noqa: E402
)
from finance.infrastructure.persistence.excel_insight_repository import (
    ExcelInsightRepository,
)  # noqa: E402
from finance.infrastructure.persistence.excel_profile_repository import (
    ExcelProfileRepository,
)  # noqa: E402
from finance.infrastructure.persistence.excel_transaction_repository import (
    ExcelTransactionRepository,
)  # noqa: E402
from finance.planilha_manager import PlanilhaManager  # noqa: E402
from finance.strategies.base_strategy import BaseMappingStrategy  # noqa: E402
from finance.strategies.default_strategy import DefaultStrategy  # noqa: E402
from infrastructure.caching.redis_cache_service import RedisCacheService  # noqa: E402

logger = get_logger("FinanceFactory")


def _load_strategy_from_file(
    strategy_path: Path, module_name: str
) -> type[BaseMappingStrategy]:
    """Carrega dinamicamente a classe de estratégia do arquivo .py do usuário."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, strategy_path)
        if spec is None:
            raise ImportError(f"Não foi possível criar spec para {strategy_path}")

        strategy_module = importlib.util.module_from_spec(spec)
        if spec.loader:
            spec.loader.exec_module(strategy_module)

        # (Remove o módulo do cache para garantir que carregamos o certo)
        sys.modules.pop(module_name, None)

        # O nome da classe é padronizado pelo StrategyGenerator
        StrategyClass = getattr(strategy_module, "CustomStrategy")
        return StrategyClass  # type: ignore[no-any-return]
    except Exception as e:
        logger.critical(f"Falha ao carregar estratégia de '{strategy_path}': {e}")
        # Retorna a Padrão como fallback de segurança
        return DefaultStrategy  # type: ignore[no-any-return]


class FinancialSystemFactory:
    """
    Factory responsável por instanciar todo o sistema financeiro (Repositories, Services, Manager)
    com as dependências corretas.
    """

    @staticmethod
    def create_manager(
        storage_handler: "BaseStorageHandler",
        config_service: "UserConfigService",
        llm_orchestrator: "LLMOrchestrator",
    ) -> PlanilhaManager:
        """
        Cria e configura uma instância completa do PlanilhaManager.
        """
        logger.debug(f"Criando sistema para usuário '{config_service.username}'")

        # 1. Cache Service
        cache_service = RedisCacheService()
        cache_key = f"dfs:{config_service.username}"

        # 2. Estratégia de Mapeamento
        mapeamento = config_service.get_mapeamento()
        strategy_instance: BaseMappingStrategy

        if mapeamento and mapeamento.get("strategy_module"):
            module_name = mapeamento["strategy_module"]
            strategy_path = config_service.strategy_file_path
            logger.debug(
                f"Carregando estratégia customizada '{module_name}' de {strategy_path}"
            )
            StrategyClass = _load_strategy_from_file(strategy_path, module_name)
            strategy_instance = StrategyClass(LAYOUT_PLANILHA, mapeamento)
        else:
            logger.debug("Usando DefaultStrategy.")
            strategy_instance = DefaultStrategy(LAYOUT_PLANILHA, None)

        # 3. Data Context
        context = FinancialDataContext(
            storage_handler=storage_handler,
            strategy=strategy_instance,
            cache_service=cache_service,
            cache_key=cache_key,
        )

        # 4. Repositories (Novo Domain Model)
        new_transaction_repo = ExcelTransactionRepository(context=context)
        transaction_domain_service = TransactionDomainService(
            repository=new_transaction_repo
        )

        new_budget_repo = ExcelBudgetRepository(context=context)
        budget_domain_service = BudgetDomainService(
            budget_repository=new_budget_repo,
            transaction_repository=new_transaction_repo,
        )

        new_category_repo = ExcelCategoryRepository(context=context)
        category_domain_service = CategoryDomainService(repository=new_category_repo)

        new_profile_repo = ExcelProfileRepository(context=context)
        new_debt_repo = ExcelDebtRepository(context=context)
        new_insight_repo = ExcelInsightRepository(context=context)
        new_goal_repo = ExcelGoalRepository(context=context)

        # --- NOVO: SERVIÇOS DE INTELIGÊNCIA ---
        embedding_service = EmbeddingService()
        semantic_category_service = SemanticCategoryService(
            embedding_service=embedding_service,
            category_repo=new_category_repo,
            cache_service=cache_service,
        )

        # 5. Use Cases
        get_profile_use_case = GetProfileUseCase(repository=new_profile_repo)
        update_profile_use_case = UpdateProfileUseCase(repository=new_profile_repo)

        add_transaction_use_case = AddTransactionUseCase(
            transaction_repo=new_transaction_repo, budget_service=budget_domain_service
        )
        update_transaction_use_case = UpdateTransactionUseCase(
            transaction_repo=new_transaction_repo, budget_service=budget_domain_service
        )
        delete_transaction_use_case = DeleteTransactionUseCase(
            transaction_repo=new_transaction_repo, budget_service=budget_domain_service
        )

        define_budget_use_case = DefineBudgetUseCase(
            budget_repo=new_budget_repo, budget_service=budget_domain_service
        )

        rename_category_use_case = RenameCategoryUseCase(
            category_service=category_domain_service,
            transaction_service=transaction_domain_service,
            budget_service=budget_domain_service,
        )

        add_or_update_debt_use_case = AddOrUpdateDebtUseCase(repository=new_debt_repo)
        add_insight_use_case = AddInsightUseCase(repository=new_insight_repo)
        add_or_update_goal_use_case = AddOrUpdateGoalUseCase(repository=new_goal_repo)
        delete_goal_use_case = DeleteGoalUseCase(repository=new_goal_repo)
        list_goals_use_case = ListGoalsUseCase(repository=new_goal_repo)
        list_budgets_use_case = ListBudgetsUseCase(repository=new_budget_repo)
        list_debts_use_case = ListDebtsUseCase(repository=new_debt_repo)
        list_transactions_use_case = ListTransactionsUseCase(
            repository=new_transaction_repo
        )
        delete_debt_use_case = DeleteDebtUseCase(repository=new_debt_repo)
        get_summary_use_case = GetSummaryUseCase(
            transaction_service=transaction_domain_service
        )
        get_expenses_by_category_use_case = GetExpensesByCategoryUseCase(
            transaction_service=transaction_domain_service
        )
        delete_budget_use_case = DeleteBudgetUseCase(
            repository=new_budget_repo, budget_service=budget_domain_service
        )
        update_budget_use_case = UpdateBudgetUseCase(
            repository=new_budget_repo, budget_service=budget_domain_service
        )
        sanitize_transactions_use_case = SanitizeTransactionsUseCase(
            llm_orchestrator=llm_orchestrator,
            category_repo=new_category_repo,
            transaction_repo=new_transaction_repo,
            transaction_service=transaction_domain_service,
        )
        generate_proactive_insights_use_case = GenerateProactiveInsightsUseCase(
            transaction_repo=new_transaction_repo,
            budget_repo=new_budget_repo,
            insight_repo=new_insight_repo,
        )

        # 5. Setup Inicial (se necessário)
        if context.is_new_file:
            logger.info("Detectado arquivo novo ou abas faltando.")
            from finance.application.services.setup_service import FinancialSetupService

            setup_service = FinancialSetupService(
                context=context,
                transaction_repo=new_transaction_repo,
                budget_repo=new_budget_repo,
                profile_repo=new_profile_repo,
            )
            if mapeamento is None:
                setup_service.populate_initial_data()
            else:
                logger.debug("Arquivo mapeado. Salvando abas do sistema...")
                context.save(add_intelligence=False)
        elif not context.is_cache_hit:
            logger.info(
                "Arquivo existente carregado do Storage. Recalculando orçamentos..."
            )
            budget_domain_service.recalculate_budgets()
        else:
            logger.info("Arquivo existente carregado do Cache. Startup rápido.")

        # --- AUTO MIGRATION CHECK ---
        # Garante que as categorias existam, mesmo se usuario nao deletar arquivo
        try:
            category_domain_service.ensure_default_categories()
        except Exception as e:
            logger.warning(f"Erro na migração automática de categorias: {e}")

        # 6. Cria o Manager (Fachada)
        return PlanilhaManager(
            context=context,
            transaction_repo=new_transaction_repo,
            budget_repo=new_budget_repo,
            debt_repo=new_debt_repo,
            profile_repo=new_profile_repo,
            insight_repo=new_insight_repo,
            category_repo=new_category_repo,
            goal_repo=new_goal_repo,
            transaction_domain_service=transaction_domain_service,
            budget_domain_service=budget_domain_service,
            category_domain_service=category_domain_service,
            get_profile_use_case=get_profile_use_case,
            update_profile_use_case=update_profile_use_case,
            add_transaction_use_case=add_transaction_use_case,
            update_transaction_use_case=update_transaction_use_case,
            delete_transaction_use_case=delete_transaction_use_case,
            define_budget_use_case=define_budget_use_case,
            rename_category_use_case=rename_category_use_case,
            add_or_update_debt_use_case=add_or_update_debt_use_case,
            add_insight_use_case=add_insight_use_case,
            add_or_update_goal_use_case=add_or_update_goal_use_case,
            delete_goal_use_case=delete_goal_use_case,
            list_goals_use_case=list_goals_use_case,
            list_budgets_use_case=list_budgets_use_case,
            list_debts_use_case=list_debts_use_case,
            list_transactions_use_case=list_transactions_use_case,
            delete_debt_use_case=delete_debt_use_case,
            get_summary_use_case=get_summary_use_case,
            get_expenses_by_category_use_case=get_expenses_by_category_use_case,
            delete_budget_use_case=delete_budget_use_case,
            update_budget_use_case=update_budget_use_case,
            sanitize_transactions_use_case=sanitize_transactions_use_case,
            generate_proactive_insights_use_case=generate_proactive_insights_use_case,
            semantic_category_service=semantic_category_service,  # INJETADO
            cache_key=cache_key,
        )
