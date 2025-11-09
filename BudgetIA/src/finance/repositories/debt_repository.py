# src/finance/repositories/debt_repository.py

import pandas as pd

import config

from ..financial_calculator import FinancialCalculator
from .data_context import FinancialDataContext


class DebtRepository:
    """
    Repositório para gerenciar TODA a lógica de
    acesso e manipulação de Dívidas.
    """

    def __init__(
        self,
        context: FinancialDataContext,
        calculator: FinancialCalculator,
    ) -> None:
        """
        Inicializa o repositório.

        Args:
            context: A Unidade de Trabalho (DataContext).
            calculator: O especialista em cálculos.
        """
        self._context = context
        self._calculator = calculator
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

        if "Nome da Dívida" not in dividas_df.columns:
            if dividas_df.empty:
                dividas_df = pd.DataFrame(
                    columns=config.LAYOUT_PLANILHA[self._aba_nome]
                )
            else:
                return "ERRO: Aba de dívidas corrompida."

        data_proximo_pgto_str = (
            data_proximo_pgto if data_proximo_pgto is not None else ""
        )

        saldo_devedor_atual = self._calculator.calcular_saldo_devedor_atual(
            valor_parcela=valor_parcela,
            taxa_juros_mensal=taxa_juros_mensal,
            parcelas_totais=parcelas_totais,
            parcelas_pagas=parcelas_pagas,
        )

        dividas_existentes = (
            dividas_df["Nome da Dívida"].astype(str).str.strip().str.lower()
        )
        nome_divida_limpo = nome_divida.strip().lower()

        idx_existente = dividas_df[dividas_existentes == nome_divida_limpo].index

        if not idx_existente.empty:
            idx = idx_existente[0]
            dividas_df.loc[idx, "Saldo Devedor Atual"] = saldo_devedor_atual
            dividas_df.loc[idx, "Taxa Juros Mensal (%)"] = taxa_juros_mensal
            dividas_df.loc[idx, "Data Próximo Pgto"] = data_proximo_pgto_str
            dividas_df.loc[idx, "Parcelas Pagas"] = parcelas_pagas
            dividas_df.loc[idx, "Observações"] = observacoes
            dividas_df.loc[idx, "Valor Original"] = valor_original
            dividas_df.loc[idx, "Parcelas Totais"] = parcelas_totais
            dividas_df.loc[idx, "Valor Parcela"] = valor_parcela
            mensagem = f"Dívida '{nome_divida}' atualizada. Saldo devedor: R$ {saldo_devedor_atual:,.2f}."
        else:
            novo_id = (
                (dividas_df["ID Divida"].max() + 1)
                if not dividas_df.empty
                and "ID Divida" in dividas_df.columns
                and dividas_df["ID Divida"].notna().any()
                else 1
            )
            nova_divida = pd.DataFrame(
                [
                    {
                        "ID Divida": novo_id,
                        "Nome da Dívida": nome_divida,
                        "Valor Original": valor_original,
                        "Saldo Devedor Atual": saldo_devedor_atual,
                        "Taxa Juros Mensal (%)": taxa_juros_mensal,
                        "Parcelas Totais": parcelas_totais,
                        "Parcelas Pagas": parcelas_pagas,
                        "Valor Parcela": valor_parcela,
                        "Data Próximo Pgto": data_proximo_pgto_str,
                        "Observações": observacoes,
                    }
                ],
                columns=config.LAYOUT_PLANILHA[self._aba_nome],
            )
            dividas_df = pd.concat([dividas_df, nova_divida], ignore_index=True)
            mensagem = f"Nova dívida '{nome_divida}' registrada com saldo inicial de R$ {saldo_devedor_atual:,.2f}."

        self._context.update_dataframe(self._aba_nome, dividas_df)
        print(f"LOG (Repo): {mensagem}")
        return str(mensagem)
