# src/finance/planilha_manager.py
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from finance.application.use_cases.add_insight_use_case import AddInsightUseCase
    from finance.application.use_cases.add_or_update_debt_use_case import (
        AddOrUpdateDebtUseCase,
    )
    from finance.application.use_cases.add_or_update_goal_use_case import (
        AddOrUpdateGoalUseCase,
    )
    from finance.application.use_cases.add_transaction_use_case import (
        AddTransactionUseCase,
    )
    from finance.application.use_cases.define_budget_use_case import DefineBudgetUseCase
    from finance.application.use_cases.delete_budget_use_case import (
        DeleteBudgetUseCase,
    )
    from finance.application.use_cases.delete_debt_use_case import (
        DeleteDebtUseCase,
    )
    from finance.application.use_cases.delete_goal_use_case import (
        DeleteGoalUseCase,
    )
    from finance.application.use_cases.delete_transaction_use_case import (
        DeleteTransactionUseCase,
    )
    from finance.application.use_cases.generate_proactive_insights_use_case import (
        GenerateProactiveInsightsUseCase,
    )
    from finance.application.use_cases.get_expenses_by_category_use_case import (
        GetExpensesByCategoryUseCase,
    )
    from finance.application.use_cases.get_profile import GetProfileUseCase
    from finance.application.use_cases.get_summary_use_case import (
        GetSummaryUseCase,
    )
    from finance.application.use_cases.list_budgets_use_case import (
        ListBudgetsUseCase,
    )
    from finance.application.use_cases.list_debts_use_case import (
        ListDebtsUseCase,
    )
    from finance.application.use_cases.list_goals_use_case import (
        ListGoalsUseCase,
    )
    from finance.application.use_cases.list_transactions_use_case import (
        ListTransactionsUseCase,
    )
    from finance.application.use_cases.rename_category_use_case import (
        RenameCategoryUseCase,
    )
    from finance.application.use_cases.sanitize_transactions_use_case import (
        SanitizeTransactionsUseCase,
    )
    from finance.application.use_cases.update_budget_use_case import (
        UpdateBudgetUseCase,
    )
    from finance.application.use_cases.update_profile import UpdateProfileUseCase
    from finance.application.use_cases.update_transaction_use_case import (
        UpdateTransactionUseCase,
    )
    from finance.domain.repositories.budget_repository import IBudgetRepository
    from finance.domain.repositories.category_repository import ICategoryRepository
    from finance.domain.repositories.data_context import FinancialDataContext
    from finance.domain.repositories.debt_repository import IDebtRepository
    from finance.domain.repositories.goal_repository import IGoalRepository
    from finance.domain.repositories.insight_repository import IInsightRepository
    from finance.domain.repositories.profile_repository import IProfileRepository
    from finance.domain.repositories.transaction_repository import (
        ITransactionRepository,
    )
    from finance.domain.services.budget_service import BudgetDomainService
    from finance.domain.services.category_service import CategoryDomainService
    from finance.domain.services.semantic_category_service import (
        SemanticCategoryService,
    )
    from finance.domain.services.transaction_service import TransactionDomainService
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
        context: FinancialDataContext,
        transaction_repo: ITransactionRepository,
        budget_repo: IBudgetRepository,
        debt_repo: IDebtRepository,
        profile_repo: IProfileRepository,
        insight_repo: IInsightRepository,
        category_repo: ICategoryRepository,
        goal_repo: IGoalRepository,
        transaction_domain_service: TransactionDomainService,
        budget_domain_service: BudgetDomainService,
        category_domain_service: CategoryDomainService,
        get_profile_use_case: GetProfileUseCase,
        update_profile_use_case: UpdateProfileUseCase,
        add_transaction_use_case: AddTransactionUseCase,
        update_transaction_use_case: UpdateTransactionUseCase,
        delete_transaction_use_case: DeleteTransactionUseCase,
        define_budget_use_case: DefineBudgetUseCase,
        rename_category_use_case: RenameCategoryUseCase,
        add_or_update_debt_use_case: AddOrUpdateDebtUseCase,
        add_insight_use_case: AddInsightUseCase,
        add_or_update_goal_use_case: AddOrUpdateGoalUseCase,
        delete_goal_use_case: DeleteGoalUseCase,
        list_goals_use_case: ListGoalsUseCase,
        list_budgets_use_case: ListBudgetsUseCase,
        list_debts_use_case: ListDebtsUseCase,
        list_transactions_use_case: ListTransactionsUseCase,
        delete_debt_use_case: DeleteDebtUseCase,
        get_summary_use_case: GetSummaryUseCase,
        get_expenses_by_category_use_case: GetExpensesByCategoryUseCase,
        delete_budget_use_case: DeleteBudgetUseCase,
        update_budget_use_case: UpdateBudgetUseCase,
        sanitize_transactions_use_case: SanitizeTransactionsUseCase,
        generate_proactive_insights_use_case: GenerateProactiveInsightsUseCase,
        semantic_category_service: SemanticCategoryService,
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
        self.category_repo = category_repo
        self.goal_repo = goal_repo
        self.generate_proactive_insights_use_case = generate_proactive_insights_use_case
        self.transaction_domain_service = transaction_domain_service
        self.budget_domain_service = budget_domain_service
        self.category_domain_service = category_domain_service
        self.get_profile_use_case = get_profile_use_case
        self.update_profile_use_case = update_profile_use_case
        self.add_transaction_use_case = add_transaction_use_case
        self.update_transaction_use_case = update_transaction_use_case
        self.delete_transaction_use_case = delete_transaction_use_case
        self.define_budget_use_case = define_budget_use_case
        self.rename_category_use_case = rename_category_use_case
        self.add_or_update_debt_use_case = add_or_update_debt_use_case
        self.add_insight_use_case = add_insight_use_case
        self.add_or_update_goal_use_case = add_or_update_goal_use_case
        self.delete_goal_use_case = delete_goal_use_case
        self.list_goals_use_case = list_goals_use_case
        self.list_budgets_use_case = list_budgets_use_case
        self.list_debts_use_case = list_debts_use_case
        self.list_transactions_use_case = list_transactions_use_case
        self.delete_debt_use_case = delete_debt_use_case
        self.get_summary_use_case = get_summary_use_case
        self.get_expenses_by_category_use_case = get_expenses_by_category_use_case
        self.delete_budget_use_case = delete_budget_use_case
        self.update_budget_use_case = update_budget_use_case
        self.sanitize_transactions_use_case = sanitize_transactions_use_case
        self.semantic_category_service = semantic_category_service
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

    def atualizar_dados(self) -> None:
        """
        Recarrega os dados do disco forçosamente para garantir
        que estamos trabalhando com a versão mais recente antes de salvar.
        Útil para transações atômicas (Lock -> Refresh -> Update -> Save).
        """
        start = time.time()
        logger.debug("Recarregando dados do disco (Atomic Refresh)...")
        dfs, _ = self._context.storage.load_sheets(
            self._context.layout_config, self._context.strategy
        )
        self._context.data = dfs
        logger.info(
            f"⏱️ PlanilhaManager.atualizar_dados concluído em {time.time() - start:.2f}s"
        )

    def salvar(self, adicionar_inteligencia: bool = False) -> None:
        self._context.save(adicionar_inteligencia)

    def save(self, adicionar_inteligencia: bool = False) -> None:
        """Alias público de salvar() para compatibilidade com os roteadores da API."""
        self.salvar(adicionar_inteligencia)

    def refresh_data(self) -> None:
        """Alias público de atualizar_dados() para compatibilidade com os roteadores da API."""
        self.atualizar_dados()

    def visualizar_dados(self, sheet_name: str) -> pd.DataFrame:
        return self._context.get_dataframe(sheet_name=sheet_name)  # type: ignore[no-any-return]

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
        parcelas: int = 1,
    ) -> None:
        """
        Adiciona uma transação via Caso de Uso.
        Mantido para compatibilidade com API e Tools.
        """
        from datetime import datetime

        from finance.domain.models.transaction import Transaction

        try:
            dt = pd.to_datetime(data)
        except:  # noqa: E722
            dt = datetime.now()

        # --- NOVO: CATEGORIZAÇÃO SEMÂNTICA ---
        # Se a categoria for genérica ou vazia, tentamos sugerir uma melhor
        categorias_genericas = [
            "Outros",
            "Desconhecido",
            "",
            "Geral",
            "Despesa",
            "Receita",
        ]
        if categoria in categorias_genericas or not categoria:
            sugestao = self.semantic_category_service.suggest_category(descricao, tipo)
            if sugestao:
                logger.info(
                    f"Categorização Inteligente: '{descricao}' -> '{sugestao.name}'"
                )
                categoria = sugestao.name

        transaction = Transaction(
            data=dt.date(),
            tipo=tipo,
            categoria=categoria,
            descricao=descricao,
            valor=valor,
            status=status,
            # Nota: 'parcelas' ainda não está no modelo de domínio Transaction
        )

        self.add_transaction_use_case.execute(transaction)
        # O Use Case já recalcula orçamentos, mas o PlanilhaManager.save()
        # ainda precisa ser chamado pelo chamador (API/Tool) ou aqui?
        # A API chama manager.save() explicitamente. As Tools também.
        # Então NÃO chamamos save() aqui para manter a atomicidade se necessário.

    def adicionar_registros_lote(self, transacoes: list[dict[str, Any]]) -> int:
        """
        Adiciona múltiplas transações delegando para o serviço de domínio.
        """
        count = 0
        for tx_data in transacoes:
            self.transaction_domain_service.add_transaction(tx_data)
            count += 1

        if count > 0:
            self.recalcular_orcamentos()
            self.salvar()
        return count

    def recalcular_orcamentos(self) -> None:
        """Recalcula orçamentos usando o domínio."""
        start = time.time()
        self.budget_domain_service.recalculate_budgets()
        logger.info(
            f"⏱️ PlanilhaManager.recalcular_orcamentos concluído em {time.time() - start:.2f}s"
        )

    def excluir_transacao(self, transacao_id: int) -> bool:
        """Remove uma transação via Caso de Uso."""
        return self.delete_transaction_use_case.execute(transacao_id)

    def faxinar_transacoes(self) -> dict[str, Any]:
        """Realiza a faxina de dados via Caso de Uso."""
        return self.sanitize_transactions_use_case.execute()

    def atualizar_transacao(self, transacao_id: int, dados: dict[str, Any]) -> bool:
        """Atualiza uma transação via Caso de Uso."""
        from finance.domain.models.transaction import Transaction

        # 1. Busca a original
        original = self.transaction_domain_service._repository.get_by_id(transacao_id)
        if not original:
            return False

        # 2. Merge de dados
        data = original.model_dump()
        data.update(dados)

        # 3. Converte para entidade (valida tipos)
        try:
            updated_entity = Transaction(**data)
            success = self.update_transaction_use_case.execute(updated_entity)
            return success is not None
        except Exception as e:
            logger.error(f"Erro ao validar transação para atualização: {e}")
            return False

    def get_summary(self) -> dict[str, float]:
        """Obtém resumo financeiro do domínio."""
        res = self.transaction_domain_service.get_summary()
        from config import SummaryKeys

        return {
            SummaryKeys.RECEITAS: res["total_receitas"],
            SummaryKeys.DESPESAS: res["total_despesas"],
            SummaryKeys.SALDO: res["saldo"],
        }

    def get_expenses_by_category(self, top_n: int = 5) -> pd.Series:
        """Obtém gastos por categoria do domínio."""
        res = self.transaction_domain_service.get_expenses_by_category(top_n)
        return pd.Series(res, dtype=float)

    def adicionar_ou_atualizar_orcamento(
        self,
        categoria: str,
        valor_limite: float,
        periodo: str = "Mensal",
        observacoes: str = "",
    ) -> str:
        """Adiciona ou atualiza orçamento via Caso de Uso."""
        from finance.domain.models.budget import Budget

        # Nota: A entidade Budget atual usa campos em português e não possui mês/ano ainda.
        budget = Budget(
            categoria=categoria,
            limite=valor_limite,
            periodo=periodo,
            observacoes=observacoes,
        )

        self.define_budget_use_case.execute(budget)
        self.salvar()
        return f"Orçamento para '{categoria}' processado com sucesso via Caso de Uso."

    def excluir_orcamento(self, budget_id: int) -> bool:
        """Deleta orçamento via Caso de Uso."""
        success = self.delete_budget_use_case.execute(budget_id)
        if success:
            self.salvar()
        return success

    def atualizar_orcamento(self, budget_id: int, dados: dict[str, Any]) -> bool:
        """Atualiza orçamento via Caso de Uso."""
        success = self.update_budget_use_case.execute(budget_id, dados)
        if success:
            self.salvar()
        return success

    def adicionar_insight_ia(
        self,
        data_insight: str,
        tipo_insight: str,
        titulo_insight: str,
        detalhes_recomendacao: str,
        status: str = "Novo",
    ) -> None:
        """Adiciona um insight via Caso de Uso."""
        from datetime import datetime

        from finance.domain.models.insight import Insight

        try:
            dt = pd.to_datetime(data_insight)
        except:  # noqa: E722
            dt = datetime.now()

        insight = Insight(
            date=dt,  # type: ignore[arg-type]
            type=tipo_insight,
            title=titulo_insight,
            details=detalhes_recomendacao,
            status=status,
        )
        self.add_insight_use_case.execute(insight)
        self.salvar()

    def salvar_dado_perfil(self, campo: str, valor: Any) -> str:
        """Salva dado de perfil via Caso de Uso."""
        self.update_profile_use_case.execute({campo: valor})
        self.salvar()
        return f"Perfil atualizado: '{campo}' definido como '{valor}'."

    def get_perfil_como_texto(self) -> str:
        """Formata o perfil para o prompt da IA via domínio."""
        profile = self.get_profile_use_case.execute()

        if (
            not profile.renda_mensal
            and not profile.objetivo_principal
            and not profile.outros_campos
        ):
            return "O perfil do usuário ainda não foi preenchido."

        contexto_str = "--- CONTEXTO DO PERFIL DO USUÁRIO (NÃO REPETIR/PERGUNTAR) ---\n"
        if profile.renda_mensal:
            contexto_str += f"- Renda Mensal Média: {profile.renda_mensal}\n"
        if profile.objetivo_principal:
            contexto_str += f"- Principal Objetivo: {profile.objetivo_principal}\n"
        if profile.tolerancia_risco:
            contexto_str += f"- Tolerância a Risco: {profile.tolerancia_risco}\n"

        for campo, valor in profile.outros_campos.items():
            if valor:
                contexto_str += f"- {campo}: {valor}\n"

        contexto_str += "--- FIM DO CONTEXTO ---"
        return contexto_str

    def ensure_profile_fields(self, fields: list[str]) -> bool:
        """Garante que campos existam via Caso de Uso."""
        # Se não existirem, adicionamos com valor None (vazio)
        profile = self.get_profile_use_case.execute()
        changed = False

        legacy_mapping = {
            "Renda Mensal Média": "renda_mensal",
            "Principal Objetivo": "objetivo_principal",
            "Tolerância a Risco": "tolerancia_risco",
        }

        for f in fields:
            field_name = legacy_mapping.get(f, f)
            if not hasattr(profile, field_name) or getattr(profile, field_name) is None:
                if field_name not in profile.outros_campos:
                    profile.outros_campos[field_name] = None
                    changed = True

        if changed:
            self.update_profile_use_case._repository.save_profile(profile)
            self.salvar()
        return changed

    def analisar_para_insights_proativos(self) -> list[dict[str, Any]]:
        logger.info("Delegando análise proativa para o Caso de Uso.")
        return self.generate_proactive_insights_use_case.execute()

    # --- NOVO: MÉTODOS DE CATEGORIAS ---
    def get_categorias(self) -> pd.DataFrame:
        """Retorna todas as categorias via domínio, mapeadas para nomes legados."""
        cats = self.category_domain_service.list_all()
        from config import ColunasCategorias

        data = [
            {
                ColunasCategorias.NOME: c.name,
                ColunasCategorias.TIPO: c.type,
                ColunasCategorias.ICONE: c.icon,
                ColunasCategorias.TAGS: c.tags,
            }
            for c in cats
        ]
        return pd.DataFrame(data)

    def adicionar_categoria(
        self, nome: str, tipo: str, icone: str = "", tags: str = ""
    ) -> bool:
        """Adiciona uma nova categoria via domínio."""
        try:
            self.category_domain_service.add_category(nome, tipo, icone, tags)
            self.salvar()
            return True
        except ValueError as e:
            logger.warning(f"Erro ao adicionar categoria: {e}")
            return False

    def excluir_categoria(self, name: str) -> bool:
        """Remove uma categoria via domínio."""
        success = self.category_domain_service.delete_category(name)
        if success:
            self.salvar()
        return success

    def atualizar_categoria(
        self, old_name: str, new_name: str, tipo: str, icone: str, tags: str
    ) -> bool:
        """Atualiza uma categoria via domínio e Caso de Uso para renomeação."""
        try:
            # 1. Se o nome mudou, dispara a cascata via Use Case PRIMEIRO
            # Isso garante que transações e orçamentos sejam atualizados antes
            # de removermos/alterarmos a categoria no repositório.
            if old_name.strip().lower() != new_name.strip().lower():
                success = self.rename_category_use_case.execute(old_name, new_name)
                if not success:
                    return False

            # 2. Atualiza propriedades básicas (tipo, icone, tags)
            # Agora usamos o new_name pois ele já é o nome atual após o RenameCase
            self.category_domain_service.update_category(
                new_name, new_name, tipo, icone, tags
            )

            self.salvar()
            return True
        except ValueError as e:
            logger.warning(f"Erro ao atualizar categoria: {e}")
            return False

    def ensure_default_categories(self) -> None:
        """Garante que existam categorias básicas via domínio."""
        self.category_domain_service.ensure_default_categories()
        self.salvar()

    def check_connection(self) -> tuple[bool, str]:
        logger.debug("Verificando saúde da conexão com o armazenamento...")
        return self._context.storage.ping()  # type: ignore[no-any-return]

    def clear_cache(self) -> None:
        logger.debug(f"Forçando invalidação de cache para '{self.cache_key}'")
        self._context.cache.delete(self.cache_key)

    # --- NOVO: MÉTODOS DE METAS ---
    def get_metas(self) -> pd.DataFrame:
        """Retorna todas as metas via domínio."""
        goals = self.list_goals_use_case.execute()
        from config import ColunasMetas

        data = [
            {
                ColunasMetas.ID: g.id,
                ColunasMetas.NOME: g.nome,
                ColunasMetas.VALOR_ALVO: g.valor_alvo,
                ColunasMetas.VALOR_ATUAL: g.valor_atual,
                ColunasMetas.DATA_ALVO: g.data_alvo,
                ColunasMetas.STATUS: g.status,
                ColunasMetas.OBS: g.observacoes,
                "Progresso (%)": g.percentual_progresso,
            }
            for g in goals
        ]
        return pd.DataFrame(data)

    def adicionar_ou_atualizar_meta(
        self,
        nome: str,
        valor_alvo: float,
        valor_atual: float = 0.0,
        data_alvo: str | None = None,
        observacoes: str = "",
        meta_id: int | None = None,
    ) -> bool:
        """Adiciona ou atualiza uma meta via domínio."""
        from finance.domain.models.goal import Goal

        try:
            dt_alvo = pd.to_datetime(data_alvo).date() if data_alvo else None
        except:  # noqa: E722
            dt_alvo = None

        goal = Goal(
            id=meta_id,
            nome=nome,
            valor_alvo=valor_alvo,
            valor_atual=valor_atual,
            data_alvo=dt_alvo,
            observacoes=observacoes,
        )

        # Atualiza status baseado no valor
        if goal.is_completed:
            goal.status = "Concluída"

        self.add_or_update_goal_use_case.execute(goal)
        self.salvar()
        return True

    def excluir_meta(self, goal_id: int) -> bool:
        """Remove uma meta via domínio."""
        success = self.delete_goal_use_case.execute(goal_id)
        if success:
            self.salvar()
        return success

    # --- NOVO: MÉTODOS DE DÍVIDAS ---
    def get_dividas(self) -> pd.DataFrame:
        """Retorna todas as dívidas via domínio."""
        debts = self.debt_repo.list_all()
        from config import ColunasDividas

        data = [
            {
                ColunasDividas.ID: d.id,
                ColunasDividas.NOME: d.nome,
                ColunasDividas.VALOR_ORIGINAL: d.valor_original,
                ColunasDividas.SALDO_DEVEDOR: d.saldo_devedor_atual,
                ColunasDividas.TAXA_JUROS: d.taxa_juros_mensal,
                ColunasDividas.PARCELAS_TOTAIS: d.parcelas_totais,
                ColunasDividas.PARCELAS_PAGAS: d.parcelas_pagas,
                ColunasDividas.VALOR_PARCELA: d.valor_parcela,
                ColunasDividas.DATA_PGTO: d.data_proximo_pgto,
                ColunasDividas.OBS: d.observacoes,
            }
            for d in debts
        ]
        return pd.DataFrame(data)

    def adicionar_ou_atualizar_divida(
        self,
        nome: str,
        valor_original: float,
        taxa_juros_mensal: float,
        parcelas_totais: int,
        valor_parcela: float,
        parcelas_pagas: int = 0,
        data_proximo_pgto: str | None = None,
        observacoes: str = "",
        divida_id: int | None = None,
    ) -> bool:
        """Adiciona ou atualiza uma dívida via domínio."""
        from finance.domain.models.debt import Debt

        try:
            dt_pgto = (
                pd.to_datetime(data_proximo_pgto).date() if data_proximo_pgto else None
            )
        except:  # noqa: E722
            dt_pgto = None

        debt = Debt(
            id=divida_id,
            nome=nome,
            valor_original=valor_original,
            taxa_juros_mensal=taxa_juros_mensal,
            parcelas_totais=parcelas_totais,
            parcelas_pagas=parcelas_pagas,
            valor_parcela=valor_parcela,
            data_proximo_pgto=dt_pgto,
            observacoes=observacoes,
        )

        self.add_or_update_debt_use_case.execute(debt)
        self.salvar()
        return True

    def excluir_divida(self, divida_id: int) -> bool:
        """Remove uma dívida via Caso de Uso."""
        success = self.delete_debt_use_case.execute(divida_id)
        if success:
            self.salvar()
        return success
