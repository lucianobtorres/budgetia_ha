# src/finance/factory.py
import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from config import LAYOUT_PLANILHA
from infrastructure.caching.redis_cache_service import RedisCacheService
from finance.planilha_manager import PlanilhaManager
from finance.repositories.budget_repository import BudgetRepository
from finance.repositories.data_context import FinancialDataContext
from finance.repositories.debt_repository import DebtRepository
from finance.repositories.insight_repository import InsightRepository
from finance.repositories.profile_repository import ProfileRepository
from finance.repositories.transaction_repository import TransactionRepository
from finance.services.budget_service import BudgetService
from finance.services.debt_service import DebtService
from finance.services.insight_service import InsightService
from finance.services.setup_service import FinancialSetupService
from finance.services.transaction_service import TransactionService
from finance.strategies.base_strategy import BaseMappingStrategy
from finance.strategies.default_strategy import DefaultStrategy

if TYPE_CHECKING:
    from core.user_config_service import UserConfigService
    from finance.storage.base_storage_handler import BaseStorageHandler


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
        return StrategyClass # type: ignore[no-any-return]
    except Exception as e:
        print(f"ERRO CRÍTICO: Falha ao carregar estratégia de '{strategy_path}': {e}")
        # Retorna a Padrão como fallback de segurança
        return DefaultStrategy # type: ignore[no-any-return]


class FinancialSystemFactory:
    """
    Factory responsável por instanciar todo o sistema financeiro (Repositories, Services, Manager)
    com as dependências corretas.
    """

    @staticmethod
    def create_manager(
        storage_handler: "BaseStorageHandler", config_service: "UserConfigService"
    ) -> PlanilhaManager:
        """
        Cria e configura uma instância completa do PlanilhaManager.
        """
        print(
            f"--- DEBUG Factory: Criando sistema para usuário '{config_service.username}' ---"
        )

        # 1. Cache Service
        # 1. Cache Service
        cache_service = RedisCacheService()
        cache_key = f"dfs:{config_service.username}"

        # 2. Estratégia de Mapeamento
        mapeamento = config_service.get_mapeamento()
        strategy_instance: BaseMappingStrategy

        if mapeamento and mapeamento.get("strategy_module"):
            module_name = mapeamento["strategy_module"]
            strategy_path = config_service.strategy_file_path
            print(
                f"--- DEBUG Factory: Carregando estratégia customizada '{module_name}' de {strategy_path} ---"
            )
            StrategyClass = _load_strategy_from_file(strategy_path, module_name)
            strategy_instance = StrategyClass(LAYOUT_PLANILHA, mapeamento)
        else:
            print("--- DEBUG Factory: Usando DefaultStrategy. ---")
            strategy_instance = DefaultStrategy(LAYOUT_PLANILHA, None)

        # 3. Data Context
        context = FinancialDataContext(
            storage_handler=storage_handler,
            strategy=strategy_instance,
            cache_service=cache_service,
            cache_key=cache_key,
        )

        # 4. Repositories & Services
        transaction_repo = TransactionRepository(
            context=context, transaction_service=TransactionService()
        )
        budget_repo = BudgetRepository(
            context=context,
            budget_service=BudgetService(),
            transaction_repo=transaction_repo,
        )
        debt_repo = DebtRepository(context=context, debt_service=DebtService())
        profile_repo = ProfileRepository(context=context)
        insight_repo = InsightRepository(context=context)

        insight_service = InsightService(
            transaction_repo=transaction_repo,
            budget_repo=budget_repo,
            insight_repo=insight_repo,
        )

        # 5. Setup Inicial (se necessário)
        if context.is_new_file:
            print("LOG: Detectado arquivo novo ou abas faltando.")
            setup_service = FinancialSetupService(
                context=context,
                transaction_repo=transaction_repo,
                budget_repo=budget_repo,
                profile_repo=profile_repo,
            )
            if mapeamento is None:
                setup_service.populate_initial_data()
            else:
                print(
                    "--- DEBUG Factory: Arquivo mapeado. Salvando abas do sistema... ---"
                )
                context.save(add_intelligence=False)
        elif not context.is_cache_hit:
            print(
                "LOG: Arquivo existente carregado do Storage. Recalculando orçamentos..."
            )
            budget_repo.recalculate_all_budgets()
        else:
            print("LOG: Arquivo existente carregado do Cache. Startup rápido.")

        # 6. Cria o Manager (Fachada)
        return PlanilhaManager(
            context=context,
            transaction_repo=transaction_repo,
            budget_repo=budget_repo,
            debt_repo=debt_repo,
            profile_repo=profile_repo,
            insight_repo=insight_repo,
            insight_service=insight_service,
            cache_key=cache_key,
        )
