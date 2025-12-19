# src/finance/repositories/debt_repository.py

import pandas as pd

import config
from config import (
    ColunasDividas,
)

from ..services.debt_service import DebtService
from .data_context import FinancialDataContext


class DebtRepository:
    """
    Repositório para gerenciar TODA a lógica de
    acesso e manipulação de Dívidas.
    """

    def __init__(
        self,
        context: FinancialDataContext,
        debt_service: DebtService,
    ) -> None:
        """
        Inicializa o repositório.

        Args:
            context: A Unidade de Trabalho (DataContext).
            calculator: O especialista em cálculos.
        """
        self._context = context
        self.debt_service = debt_service
        self._aba_nome = config.NomesAbas.DIVIDAS

    def add_or_update_debt(
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
        """
        Adiciona ou atualiza uma dívida na aba 'Minhas Dívidas'.
        Delega o cálculo do saldo devedor para o FinancialCalculator.
        """
        dividas_df = self._context.get_dataframe(self._aba_nome)

        if ColunasDividas.NOME not in dividas_df.columns:
            if dividas_df.empty:
                dividas_df = pd.DataFrame(
                    columns=config.LAYOUT_PLANILHA[self._aba_nome]
                )
            else:
                return "ERRO: Aba de dívidas corrompida."

        data_proximo_pgto_str = (
            data_proximo_pgto if data_proximo_pgto is not None else ""
        )

        saldo_devedor_atual = self.debt_service.calcular_saldo_devedor_atual(
            valor_parcela=valor_parcela,
            taxa_juros_mensal=taxa_juros_mensal,
            parcelas_totais=parcelas_totais,
            parcelas_pagas=parcelas_pagas,
        )

        dividas_existentes = (
            dividas_df[ColunasDividas.NOME].astype(str).str.strip().str.lower()
        )
        nome_divida_limpo = nome_divida.strip().lower()

        idx_existente = dividas_df[dividas_existentes == nome_divida_limpo].index

        if not idx_existente.empty:
            idx = idx_existente[0]
            dividas_df.loc[idx, ColunasDividas.SALDO_DEVEDOR] = saldo_devedor_atual
            dividas_df.loc[idx, ColunasDividas.TAXA_JUROS] = taxa_juros_mensal
            dividas_df.loc[idx, ColunasDividas.DATA_PGTO] = pd.to_datetime(data_proximo_pgto, errors='coerce')
            dividas_df.loc[idx, ColunasDividas.PARCELAS_PAGAS] = parcelas_pagas
            dividas_df.loc[idx, ColunasDividas.OBS] = observacoes
            dividas_df.loc[idx, ColunasDividas.VALOR_ORIGINAL] = valor_original
            dividas_df.loc[idx, ColunasDividas.PARCELAS_TOTAIS] = parcelas_totais
            dividas_df.loc[idx, ColunasDividas.VALOR_PARCELA] = valor_parcela
            mensagem = f"Dívida '{nome_divida}' atualizada. Saldo devedor: R$ {saldo_devedor_atual:,.2f}."
        else:
            novo_id = (
                (dividas_df[ColunasDividas.ID].max() + 1)
                if not dividas_df.empty
                and ColunasDividas.ID in dividas_df.columns
                and dividas_df[ColunasDividas.ID].notna().any()
                else 1
            )
            nova_divida = pd.DataFrame(
                [
                    {
                        ColunasDividas.ID: novo_id,
                        ColunasDividas.NOME: nome_divida,
                        ColunasDividas.VALOR_ORIGINAL: valor_original,
                        ColunasDividas.SALDO_DEVEDOR: saldo_devedor_atual,
                        ColunasDividas.TAXA_JUROS: taxa_juros_mensal,
                        ColunasDividas.PARCELAS_TOTAIS: parcelas_totais,
                        ColunasDividas.PARCELAS_PAGAS: parcelas_pagas,
                        ColunasDividas.VALOR_PARCELA: valor_parcela,
                        ColunasDividas.DATA_PGTO: pd.to_datetime(data_proximo_pgto, errors='coerce'),
                        ColunasDividas.OBS: observacoes,
                    }
                ],
                columns=config.LAYOUT_PLANILHA[self._aba_nome],
            )
            dividas_df = pd.concat([dividas_df, nova_divida], ignore_index=True)
            mensagem = f"Nova dívida '{nome_divida}' registrada com saldo inicial de R$ {saldo_devedor_atual:,.2f}."

        self._context.update_dataframe(self._aba_nome, dividas_df)
        print(f"LOG (Repo): {mensagem}")
        return str(mensagem)
