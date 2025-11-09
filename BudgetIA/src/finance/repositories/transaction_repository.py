# src/finance/repositories/transaction_repository.py
import pandas as pd

import config

# Imports relativos para "subir" um nível
from ..financial_calculator import FinancialCalculator
from .data_context import FinancialDataContext


class TransactionRepository:
    """
    Repositório para gerenciar TODA a lógica de
    acesso e manipulação de Transações.
    """

    def __init__(
        self,
        context: FinancialDataContext,
        calculator: FinancialCalculator,
    ) -> None:
        """
        Inicializa o repositório.

        Args:
            context: A Unidade de Trabalho (DataContext) que gerencia os DataFrames.
            calculator: O especialista em cálculos financeiros puros.
        """
        self._context = context
        self._calculator = calculator
        self._aba_nome = config.NomesAbas.TRANSACOES

    def get_all_transactions(self) -> pd.DataFrame:
        """Retorna o DataFrame completo de transações."""
        return self._context.get_dataframe(self._aba_nome)

    def add_transaction(
        self,
        data: str,
        tipo: str,
        categoria: str,
        descricao: str,
        valor: float,
        status: str = "Concluído",
    ) -> None:
        """
        Adiciona uma nova transação ao DataFrame em memória (no DataContext).
        """
        df = self.get_all_transactions()  # Pega a cópia atual

        novo_id = (
            (df["ID Transacao"].max() + 1)
            if not df.empty
            and "ID Transacao" in df.columns
            and df["ID Transacao"].notna().any()
            else 1
        )

        novo_registro = pd.DataFrame(
            [
                {
                    "ID Transacao": novo_id,
                    "Data": data,
                    "Tipo (Receita/Despesa)": tipo,
                    "Categoria": categoria,
                    "Descricao": descricao,
                    "Valor": valor,
                    "Status": status,
                }
            ],
            columns=config.LAYOUT_PLANILHA[self._aba_nome],
        )

        df_atualizado = pd.concat([df, novo_registro], ignore_index=True)

        self._context.update_dataframe(self._aba_nome, df_atualizado)
        print(f"LOG (Repo): Transação '{descricao}' adicionada ao contexto.")

    def get_summary(self) -> dict[str, float]:
        """Delega o cálculo do resumo para o FinancialCalculator."""
        df_transacoes = self.get_all_transactions()
        return self._calculator.get_summary(df_transacoes)

    def get_expenses_by_category(self, top_n: int = 5) -> pd.Series:
        """Delega o cálculo das despesas por categoria para o FinancialCalculator."""
        df_transacoes = self.get_all_transactions()
        return self._calculator.get_expenses_by_category(df_transacoes, top_n)
