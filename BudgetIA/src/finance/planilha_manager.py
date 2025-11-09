# src/finance/planilha_manager.py
import datetime
from typing import Any

import pandas as pd

import config

from .excel_handler import ExcelHandler
from .financial_calculator import FinancialCalculator
from .repositories.budget_repository import BudgetRepository

# Importa todos os repositórios
from .repositories.data_context import FinancialDataContext
from .repositories.debt_repository import DebtRepository
from .repositories.insight_repository import InsightRepository
from .repositories.profile_repository import ProfileRepository
from .repositories.transaction_repository import TransactionRepository
from .utils import _carregar_dados_exemplo


class PlanilhaManager:
    """
    Orquestra os dados financeiros. (Fachada)
    Sua única responsabilidade é construir os repositórios
    e delegar chamadas para eles.
    """

    def __init__(
        self,
        excel_handler: ExcelHandler,
        mapeamento: dict[str, Any] | None = None,
    ) -> None:
        """
        Inicializa o gerenciador, o DataContext e todos os Repositórios.
        """
        self._context = FinancialDataContext(
            excel_handler=excel_handler, mapeamento=mapeamento
        )
        self.calculator = FinancialCalculator()
        self.is_new_file = self._context.is_new_file

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

    # --- MÉTODOS DE PERSISTÊNCIA E ACESSO (DELEGADOS) ---

    def save(self, add_intelligence: bool = False) -> None:
        """Delega a tarefa de salvar para o DataContext."""
        self._context.save(add_intelligence)

    def visualizar_dados(self, aba_nome: str) -> pd.DataFrame:
        """Delega a visualização de dados para o DataContext."""
        return self._context.get_dataframe(aba_nome)

    def update_dataframe(self, sheet_name: str, new_df: pd.DataFrame) -> None:
        """Delega a atualização de dados para o DataContext."""
        self._context.update_dataframe(sheet_name, new_df)

    # --- MÉTODOS DE TRANSAÇÃO (DELEGADOS) ---

    def adicionar_registro(
        self,
        data: str,
        tipo: str,
        categoria: str,
        descricao: str,
        valor: float,
        status: str = "Concluído",
    ) -> None:
        """Delega a adição para o Repo e recalcula orçamentos."""
        self.transaction_repo.add_transaction(
            data, tipo, categoria, descricao, valor, status
        )
        self.recalculate_budgets()

    def get_summary(self) -> dict[str, float]:
        """Delega o cálculo do resumo para o TransactionRepository."""
        return self.transaction_repo.get_summary()

    def get_expenses_by_category(self, top_n: int = 5) -> pd.Series:
        """Delega o cálculo das despesas por categoria para o TransactionRepository."""
        return self.transaction_repo.get_expenses_by_category(top_n)

    # --- MÉTODOS DE ORÇAMENTO (DELEGADOS) ---

    def adicionar_ou_atualizar_orcamento(
        self,
        categoria: str,
        valor_limite: float,
        periodo: str = "Mensal",
        observacoes: str = "",
    ) -> str:
        """Delega a lógica de adicionar/atualizar e orquestra o recálculo."""
        mensagem = self.budget_repo.add_or_update_budget(
            categoria=categoria,
            valor_limite=valor_limite,
            periodo=periodo,
            observacoes=observacoes,
        )
        self.recalculate_budgets()
        return mensagem

    def recalculate_budgets(self) -> None:
        """Delega a lógica de recálculo para o BudgetRepository."""
        self.budget_repo.recalculate_all_budgets()

    # --- MÉTODOS DE DÍVIDA (DELEGADOS) ---

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
        """Delega a lógica de adicionar/atualizar para o DebtRepository."""
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

    # --- MÉTODOS DE INSIGHT (DELEGADOS) ---

    def adicionar_insight_ia(
        self,
        data_insight: str,
        tipo_insight: str,
        titulo_insight: str,
        detalhes_recomendacao: str,
        status: str = "Novo",
    ) -> None:
        """Delega a adição de insight para o InsightRepository."""
        self.insight_repo.add_insight(
            data_insight=data_insight,
            tipo_insight=tipo_insight,
            titulo_insight=titulo_insight,
            detalhes_recomendacao=detalhes_recomendacao,
            status=status,
        )

    # --- MÉTODOS DE PERFIL (DELEGADOS) ---

    def salvar_dado_perfil(self, campo: str, valor: Any) -> str:
        """Delega a lógica de salvar/atualizar para o ProfileRepository."""
        return self.profile_repo.save_profile_field(campo=campo, valor=valor)

    def get_perfil_como_texto(self) -> str:
        """Delega a lógica de formatação do perfil para o ProfileRepository."""
        return self.profile_repo.get_profile_as_text()

    # --- MÉTODOS DE ORQUESTRAÇÃO (Ainda vivem aqui) ---

    def analisar_para_insights_proativos(self) -> list[dict[str, Any]]:
        """Orquestra a geração de insights proativos."""
        print("LOG: Orquestrando análise proativa para gerar insights.")
        self.recalculate_budgets()

        resumo = self.get_summary()  # Delegado
        saldo_total = resumo.get("saldo", 0.0)
        orcamentos_df = self._context.get_dataframe(config.NomesAbas.ORCAMENTOS)

        insights_gerados = self.calculator.gerar_analise_proativa(
            orcamentos_df, saldo_total
        )

        if insights_gerados:
            print(f"LOG: {len(insights_gerados)} insights gerados. Registrando...")
            for insight in insights_gerados:
                # Usa o repo para adicionar
                self.insight_repo.add_insight(
                    data_insight=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    tipo_insight=insight["tipo_insight"],
                    titulo_insight=insight["titulo_insight"],
                    detalhes_recomendacao=insight["detalhes_recomendacao"],
                )
        else:
            print("LOG: Análise proativa concluída. Nenhum insight novo gerado.")

        return insights_gerados

    def _populate_initial_data(self) -> None:
        """Popula a planilha com dados de exemplo se estiver vazia."""
        print("--- DEBUG PM: Populando com dados de exemplo... ---")

        # 1. Orçamentos
        if self.visualizar_dados(config.NomesAbas.ORCAMENTOS).empty:
            orcamentos_dicts = [
                {
                    "Categoria": "Alimentação",
                    "Valor Limite Mensal": 600.0,
                    "Período Orçamento": "Mensal",
                    "Observações": "",
                },
                {
                    "Categoria": "Transporte",
                    "Valor Limite Mensal": 250.0,
                    "Período Orçamento": "Mensal",
                    "Observações": "",
                },
            ]
            for o in orcamentos_dicts:
                # Chama o método delegado (que recalcula)
                self.adicionar_ou_atualizar_orcamento(
                    categoria=o["Categoria"],
                    valor_limite=o["Valor Limite Mensal"],
                    periodo=o["Período Orçamento"],
                    observacoes=o.get("Observações", ""),
                )

        # 2. Transações
        if self.visualizar_dados(config.NomesAbas.TRANSACOES).empty:
            transacoes_exemplo = _carregar_dados_exemplo(config.DADOS_EXEMPLO_PATH)
            if not transacoes_exemplo:
                transacoes_exemplo = [
                    {
                        "data": "2024-07-01",
                        "tipo": "Receita",
                        "categoria": "Salário",
                        "descricao": "Pagamento",
                        "valor": 5000.0,
                        "status": "Concluído",
                    },
                    {
                        "data": "2024-07-05",
                        "tipo": "Despesa",
                        "categoria": "Moradia",
                        "descricao": "Aluguel",
                        "valor": 1500.0,
                        "status": "Concluído",
                    },
                ]

            for t in transacoes_exemplo:
                # Adiciona sem recalcular cada vez
                self.transaction_repo.add_transaction(
                    data=t["data"],
                    tipo=t["tipo"],
                    categoria=t["categoria"],
                    descricao=t.get("descricao", ""),
                    valor=t["valor"],
                    status=t.get("status", "Concluído"),
                )

            self.recalculate_budgets()  # Recalcula UMA VEZ no final

        # 3. Perfil
        print("--- DEBUG PM: Garantindo campos de perfil... ---")
        self_df_perfil = self.visualizar_dados(config.NomesAbas.PERFIL_FINANCEIRO)
        campos_existentes = (
            set(self_df_perfil["Campo"].astype(str).str.lower())
            if "Campo" in self_df_perfil.columns
            else set()
        )

        if "renda mensal média" not in campos_existentes:
            self.profile_repo.save_profile_field("Renda Mensal Média", None)
        if "principal objetivo" not in campos_existentes:
            self.profile_repo.save_profile_field("Principal Objetivo", None)
