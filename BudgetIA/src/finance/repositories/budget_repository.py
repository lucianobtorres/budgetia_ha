# src/finance/repositories/budget_repository.py
import pandas as pd

import config
from config import ColunasOrcamentos

from ..services.budget_service import BudgetService
from .data_context import FinancialDataContext
from .transaction_repository import TransactionRepository


class BudgetRepository:
    """
    Repositório para gerenciar TODA a lógica de
    acesso e manipulação de Orçamentos.
    """

    def __init__(
        self,
        context: FinancialDataContext,
        budget_service: BudgetService,
        transaction_repo: TransactionRepository,
    ) -> None:
        """
        Inicializa o repositório.
        """
        self._context = context
        self._budget_service = budget_service
        self._transaction_repo = transaction_repo
        self._aba_nome = config.NomesAbas.ORCAMENTOS

    def add_or_update_budget(
        self,
        categoria: str,
        valor_limite: float,
        periodo: str = "Mensal",
        observacoes: str = "",
    ) -> str:
        """Adiciona ou atualiza um orçamento em memória (sem recalcular)."""
        df = self._context.get_dataframe(self._aba_nome)

        if (
            ColunasOrcamentos.CATEGORIA not in df.columns
            or ColunasOrcamentos.PERIODO not in df.columns
        ):
            if df.empty:
                df = pd.DataFrame(columns=config.LAYOUT_PLANILHA[self._aba_nome])
            else:
                return "ERRO: Aba de orçamentos corrompida."

        categorias_existentes = (
            df[ColunasOrcamentos.CATEGORIA].astype(str).str.strip().str.lower()
        )
        periodos_existentes = (
            df[ColunasOrcamentos.PERIODO].astype(str).str.strip().str.lower()
        )
        categoria_limpa = categoria.strip().lower()
        periodo_limpo = periodo.strip().lower()

        idx_existente = df[
            (categorias_existentes == categoria_limpa)
            & (periodos_existentes == periodo_limpo)
        ].index

        if not idx_existente.empty:
            idx = idx_existente[0]
            df.loc[idx, ColunasOrcamentos.LIMITE] = valor_limite
            df.loc[idx, ColunasOrcamentos.OBS] = observacoes
            mensagem = f"Orçamento para '{categoria}' atualizado."
        else:
            novo_id = (
                (df[ColunasOrcamentos.ID].max() + 1)
                if not df.empty
                and ColunasOrcamentos.ID in df.columns
                and df[ColunasOrcamentos.ID].notna().any()
                else 1
            )
            novo_orcamento = pd.DataFrame(
                [
                    {
                        ColunasOrcamentos.ID: novo_id,
                        ColunasOrcamentos.CATEGORIA: categoria,
                        ColunasOrcamentos.GASTO: valor_limite,
                        ColunasOrcamentos.PERIODO: periodo,
                        ColunasOrcamentos.OBS: observacoes,
                    }
                ],
                columns=config.LAYOUT_PLANILHA[self._aba_nome],
            )
            df = pd.concat([df, novo_orcamento], ignore_index=True).fillna(
                {ColunasOrcamentos.GASTO: 0, ColunasOrcamentos.PERCENTUAL: 0}
            )
            mensagem = f"Novo orçamento para '{categoria}' criado."

        self._context.update_dataframe(self._aba_nome, df)

        # --- CORREÇÃO: REMOVER ESTA LINHA ---
        # A orquestração não pertence ao repositório.
        # self.recalculate_all_budgets()
        # --- FIM DA CORREÇÃO ---

        return mensagem

    def recalculate_all_budgets(self) -> None:
        """
        Delega o recálculo dos orçamentos para o FinancialCalculator,
        buscando os dados frescos dos repositórios.
        """
        df_transacoes = self._transaction_repo.get_all_transactions()
        df_orcamentos = self._context.get_dataframe(self._aba_nome)

        df_orcamentos_atualizado = self._budget_service.calcular_status_orcamentos(
            df_transacoes=df_transacoes,
            df_orcamentos=df_orcamentos,
        )
        self._context.update_dataframe(self._aba_nome, df_orcamentos_atualizado)

        print(
            "--- DEBUG (BudgetRepo): Solicitando salvamento do orçamento atualizado... ---"
        )
        self._context.save()
