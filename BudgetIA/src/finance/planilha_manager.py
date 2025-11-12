# src/finance/planilha_manager.py
import datetime
import logging
from typing import Any

import pandas as pd

from config import DADOS_EXEMPLO_PATH, ColunasOrcamentos, ColunasTransacoes, NomesAbas

from .financial_calculator import FinancialCalculator
from .repositories.budget_repository import BudgetRepository
from .repositories.data_context import FinancialDataContext
from .repositories.debt_repository import DebtRepository
from .repositories.insight_repository import InsightRepository
from .repositories.profile_repository import ProfileRepository
from .repositories.transaction_repository import TransactionRepository

# --- 1. REMOVER O IMPORT CONCRETO ---
# from .excel_handler import ExcelHandler
# --- 2. ADICIONAR O IMPORT DA INTERFACE ---
from .storage.base_storage_handler import BaseStorageHandler
from .utils import _carregar_dados_exemplo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlanilhaManager:
    """
    Orquestra os dados financeiros. (Fachada)
    Sua única responsabilidade é construir os repositórios
    e delegar chamadas para eles.
    """

    def __init__(
        self,
        # --- 3. MUDAR O TIPO DA DEPENDÊNCIA ---
        storage_handler: BaseStorageHandler,
        # (O nome do argumento muda de 'excel_handler' para 'storage_handler')
        mapeamento: dict[str, Any] | None = None,
    ) -> None:
        """
        Inicializa o gerenciador, o DataContext e todos os Repositórios.
        """
        # --- 4. INJETAR O HANDLER ABSTRATO NO DATACONTEXT ---
        self._context = FinancialDataContext(
            storage_handler=storage_handler, mapeamento=mapeamento
        )
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
        else:
            print("LOG: Arquivo existente carregado. Recalculando orçamentos...")
            self.recalculate_budgets()

    # --- O RESTO DO ARQUIVO (TODOS OS MÉTODOS DELEGADOS) ---
    # --- PERMANECE EXATAMENTE IGUAL ---

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
