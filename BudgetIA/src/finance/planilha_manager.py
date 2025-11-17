# src/finance/planilha_manager.py
import datetime

# --- NOVOS IMPORTS NECESSÁRIOS ---
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# --- FIM NOVOS IMPORTS ---
from config import (
    DADOS_EXEMPLO_PATH,
    LAYOUT_PLANILHA,
    ColunasOrcamentos,
    ColunasTransacoes,
    NomesAbas,
)
from core.cache_service import CacheService

# --- IMPORT DO CONFIG SERVICE ---
from core.user_config_service import UserConfigService

# --- FIM IMPORT ---
from .financial_calculator import FinancialCalculator
from .repositories.budget_repository import BudgetRepository

# --- DATA CONTEXT AGORA É IMPORTADO ASSIM ---
from .repositories.data_context import FinancialDataContext

# --- FIM IMPORT ---
from .repositories.debt_repository import DebtRepository
from .repositories.insight_repository import InsightRepository
from .repositories.profile_repository import ProfileRepository
from .repositories.transaction_repository import TransactionRepository
from .storage.base_storage_handler import BaseStorageHandler

# --- IMPORTS DE ESTRATÉGIA (BASE E DEFAULT) ---
from .strategies.base_strategy import BaseMappingStrategy
from .strategies.default_strategy import DefaultStrategy
from .utils import _carregar_dados_exemplo

# --- FIM IMPORTS ---


def _load_strategy_from_file(
    strategy_path: Path, module_name: str
) -> type[BaseMappingStrategy]:  # Retorna a *classe*
    """Carrega dinamicamente a classe de estratégia do arquivo .py do usuário."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, strategy_path)
        if spec is None:
            raise ImportError(f"Não foi possível criar spec para {strategy_path}")

        strategy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy_module)

        # (Remove o módulo do cache para garantir que carregamos o certo)
        sys.modules.pop(module_name, None)

        # O nome da classe é padronizado pelo StrategyGenerator
        StrategyClass = getattr(strategy_module, "CustomStrategy")
        return StrategyClass
    except Exception as e:
        print(f"ERRO CRÍTICO: Falha ao carregar estratégia de '{strategy_path}': {e}")
        # Retorna a Padrão como fallback de segurança
        return DefaultStrategy


class PlanilhaManager:
    """
    Orquestra os dados financeiros. (Fachada)
    Sua única responsabilidade é construir os repositórios
    e delegar chamadas para eles.
    """

    def __init__(
        self,
        storage_handler: BaseStorageHandler,
        config_service: UserConfigService,  # <-- Injeta o ConfigService
        # (Removido 'mapeamento')
    ) -> None:
        """
        Inicializa o gerenciador, o DataContext e todos os Repositórios.
        """
        print(
            f"--- DEBUG PM: PlanilhaManager inicializado para usuário '{config_service.username}' ---"
        )

        # --- 2. INSTANCIAR O CACHE SERVICE ---
        # (O CacheService já lê o config.UPSTASH_REDIS_URL)
        self.cache_service = CacheService()
        # Define uma chave de cache única para este usuário
        self.cache_key = f"dfs:{config_service.username}"
        # --- FIM DA INSTANCIAÇÃO ---

        mapeamento = config_service.get_mapeamento()
        strategy_instance: BaseMappingStrategy

        if mapeamento and mapeamento.get("strategy_module"):
            module_name = mapeamento["strategy_module"]
            strategy_path = config_service.strategy_file_path

            print(
                f"--- DEBUG PM: Carregando estratégia customizada '{module_name}' de {strategy_path} ---"
            )

            StrategyClass = _load_strategy_from_file(strategy_path, module_name)
            strategy_instance = StrategyClass(LAYOUT_PLANILHA, mapeamento)
        else:
            print(
                "--- DEBUG PM: Mapeamento não encontrado. Usando DefaultStrategy. ---"
            )
            strategy_instance = DefaultStrategy(LAYOUT_PLANILHA, None)

        self._context = FinancialDataContext(
            storage_handler=storage_handler,
            strategy=strategy_instance,
            cache_service=self.cache_service,
            cache_key=self.cache_key,
        )

        self.is_new_file = self._context.is_new_file

        self.calculator = FinancialCalculator()
        self.is_new_file = self._context.is_new_file

        # --- LOG ADICIONADO ---
        print(
            f"--- DEBUG (PlanilhaManager): 'self.is_new_file' (vindo do context) é: {self.is_new_file} ---"
        )
        # --- FIM DO LOG ---

        # --- CRIA TODOS OS REPOSITÓRIOS ---
        self.transaction_repo = TransactionRepository(
            context=self._context, calculator=self.calculator
        )
        self.budget_repo = BudgetRepository(
            context=self._context,
            calculator=self.calculator,
            transaction_repo=self.transaction_repo,
        )
        self.debt_repo = DebtRepository(
            context=self._context, calculator=self.calculator
        )
        self.profile_repo = ProfileRepository(context=self._context)
        self.insight_repo = InsightRepository(context=self._context)
        # --- FIM DA CRIAÇÃO ---

        if self.is_new_file:
            print("LOG: Detectado arquivo novo ou abas faltando.")
            if mapeamento is None:
                print(
                    "--- DEBUG PM: Arquivo novo padrão. Populando com dados de exemplo... ---"
                )
                self._populate_initial_data()
                self._context.save(add_intelligence=True)
            else:
                print(
                    "--- DEBUG PM: Arquivo mapeado/novo. Salvando abas do sistema... ---"
                )
                self._context.save(add_intelligence=False)
        elif not self._context.is_cache_hit:
            print(
                "LOG: Arquivo existente carregado do Storage. Recalculando orçamentos..."
            )
            self.recalculate_budgets()
        else:
            print("LOG: Arquivo existente carregado do Cache. Startup rápido.")

    # ... (save) ...
    def save(self, add_intelligence: bool = False) -> None:
        self._context.save(add_intelligence)

    # ... (visualizar_dados) ...
    def visualizar_dados(self, aba_nome: str) -> pd.DataFrame:
        return self._context.get_dataframe(sheet_name=aba_nome)

    # ... (update_dataframe) ...
    def update_dataframe(self, sheet_name: str, new_df: pd.DataFrame) -> None:
        self._context.update_dataframe(sheet_name, new_df)

    # ... (adicionar_registro) ...
    def adicionar_registro(
        self,
        data: str,
        tipo: str,
        categoria: str,
        descricao: str,
        valor: float,
        status: str = "Concluído",
    ) -> None:
        self.transaction_repo.add_transaction(
            data, tipo, categoria, descricao, valor, status
        )
        self.recalculate_budgets()

    # ... (get_summary) ...
    def get_summary(self) -> dict[str, float]:
        return self.transaction_repo.get_summary()

    # ... (get_expenses_by_category) ...
    def get_expenses_by_category(self, top_n: int = 5) -> pd.Series:
        return self.transaction_repo.get_expenses_by_category(top_n)

    # ... (adicionar_ou_atualizar_orcamento) ...
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
        return mensagem

    # ... (recalculate_budgets) ...
    def recalculate_budgets(self) -> None:
        self.budget_repo.recalculate_all_budgets()

    # ... (adicionar_ou_atualizar_divida) ...
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
        return self.debt_repo.add_or_update_debt(
            nome_divida=nome_divida,
            valor_original=valor_original,
            taxa_juros_mensal=taxa_juros_mensal,
            parcelas_totais=parcelas_totais,
            valor_parcela=valor_parcela,
            parcelas_pagas=parcelas_pagas,
            data_proximo_pgto=data_proximo_pgto,
            observacoes=observacoes,
        )

    # ... (adicionar_insight_ia) ...
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

    # ... (salvar_dado_perfil) ...
    def salvar_dado_perfil(self, campo: str, valor: Any) -> str:
        return self.profile_repo.save_profile_field(campo=campo, valor=valor)

    # ... (get_perfil_como_texto) ...
    def get_perfil_como_texto(self) -> str:
        return self.profile_repo.get_profile_as_text()

    # ... (analisar_para_insights_proativos) ...
    def analisar_para_insights_proativos(self) -> list[dict[str, Any]]:
        print("LOG: Orquestrando análise proativa para gerar insights.")
        self.recalculate_budgets()
        resumo = self.get_summary()  # Delegado
        saldo_total = resumo.get("saldo", 0.0)
        orcamentos_df = self._context.get_dataframe(NomesAbas.ORCAMENTOS)
        insights_gerados = self.calculator.gerar_analise_proativa(
            orcamentos_df, saldo_total
        )
        if insights_gerados:
            print(f"LOG: {len(insights_gerados)} insights gerados. Registrando...")
            for insight in insights_gerados:
                self.insight_repo.add_insight(
                    data_insight=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    tipo_insight=insight["tipo_insight"],
                    titulo_insight=insight["titulo_insight"],
                    detalhes_recomendacao=insight["detalhes_recomendacao"],
                )
        else:
            print("LOG: Análise proativa concluída. Nenhum insight novo gerado.")
        return insights_gerados

    # ... (_populate_initial_data) ...
    def _populate_initial_data(self) -> None:
        print("--- DEBUG PM: Populando com dados de exemplo... ---")
        if self.visualizar_dados(NomesAbas.ORCAMENTOS).empty:
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
                self.adicionar_ou_atualizar_orcamento(
                    categoria=o[ColunasOrcamentos.CATEGORIA],
                    valor_limite=o[ColunasOrcamentos.LIMITE],
                    periodo=o[ColunasOrcamentos.PERIODO],
                    observacoes=o.get(ColunasOrcamentos.OBS, ""),
                )
        if self.visualizar_dados(NomesAbas.TRANSACOES).empty:
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
                self.transaction_repo.add_transaction(
                    data=t["data"],
                    tipo=t["tipo"],
                    categoria=t[ColunasOrcamentos.CATEGORIA],
                    descricao=t.get("descricao", ""),
                    valor=t["valor"],
                    status=t.get("status", "Concluído"),
                )
            self.recalculate_budgets()
        print("--- DEBUG PM: Garantindo campos de perfil... ---")
        self_df_perfil = self.visualizar_dados(NomesAbas.PERFIL_FINANCEIRO)
        campos_existentes = (
            set(self_df_perfil["Campo"].astype(str).str.lower())
            if "Campo" in self_df_perfil.columns
            else set()
        )
        if "renda mensal média" not in campos_existentes:
            self.profile_repo.save_profile_field("Renda Mensal Média", None)
        if "principal objetivo" not in campos_existentes:
            self.profile_repo.save_profile_field("Principal Objetivo", None)

    def check_connection(self) -> tuple[bool, str]:
        """
        Delega a verificação de conexão para o handler de armazenamento.
        """
        print("--- DEBUG PM: Verificando saúde da conexão com o armazenamento... ---")
        return self._context.storage.ping()

    def clear_cache(self) -> None:
        """
        Força a invalidação (deleção) do cache deste usuário no Redis.
        A próxima leitura será forçada a buscar do Google Drive.
        """
        print(
            f"--- DEBUG PM: Forçando invalidação de cache para '{self.cache_key}' ---"
        )
        self._context.cache.delete(self.cache_key)
