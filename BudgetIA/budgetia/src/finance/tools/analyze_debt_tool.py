# src/finance/tools/analyze_debt_tool.py
from collections.abc import Callable  # Importar Callable

import pandas as pd
from numpy_financial import ipmt, nper
from pydantic import BaseModel

from config import ColunasDividas, NomesAbas
from core.base_tool import BaseTool
from finance.schemas import AnalisarDividaInput


class AnalisarDividaTool(BaseTool):  # type: ignore[misc]
    name: str = "analisar_divida"
    description: str = (
        "Analisa uma dívida específica e sugere estratégias de quitação. "
        "Calcula o saldo devedor atual e projeta o tempo para quitação."
    )
    args_schema: type[BaseModel] = AnalisarDividaInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self, nome_divida: str) -> str:
        print(
            f"LOG: Ferramenta '{self.name}' chamada para analisar dívida: {nome_divida}."
        )

        # --- DIP: Chama a função injetada ---
        df = self.visualizar_dados(aba_nome=NomesAbas.DIVIDAS)
        if df.empty:
            return (
                "A aba de dívidas está vazia. Nenhuma dívida encontrada para análise."
            )

        divida_encontrada = df[
            df[ColunasDividas.NOME].astype(str).str.lower() == nome_divida.lower()
        ]

        if divida_encontrada.empty:
            return f"Dívida '{nome_divida}' não encontrada na planilha."

        divida = divida_encontrada.iloc[0]

        try:
            saldo_devedor = float(divida[ColunasDividas.SALDO_DEVEDOR])
            taxa_juros_mensal = float(divida[ColunasDividas.TAXA_JUROS]) / 100
            valor_parcela = float(divida[ColunasDividas.VALOR_PARCELA])
            parcelas_totais = int(divida[ColunasDividas.PARCELAS_PAGAS])
            parcelas_pagas = int(divida[ColunasDividas.PARCELAS_PAGAS])

            if saldo_devedor <= 0:
                return f"A dívida '{nome_divida}' já está quitada."

            # Calcula juros da primeira parcela restante
            juros_primeira_parcela = -ipmt(
                taxa_juros_mensal, 1, (parcelas_totais - parcelas_pagas), saldo_devedor
            )

            if valor_parcela <= juros_primeira_parcela and taxa_juros_mensal > 0:
                return (
                    f"AVISO: A parcela de R$ {valor_parcela:,.2f} da sua dívida '{nome_divida}' "
                    f"é insuficiente para cobrir os juros mensais (aprox. R$ {juros_primeira_parcela:,.2f}). "
                    "Isso pode fazer sua dívida crescer. Recomendo negociar com o credor."
                )

            # Projeta o número de meses para quitação
            meses_restantes = nper(taxa_juros_mensal, -valor_parcela, saldo_devedor)

            # Sugestão de amortização (pagar um extra)
            extra_sugerido = max(50.0, valor_parcela * 0.1)  # Sugere 10% ou 50 reais
            parcela_com_extra = valor_parcela + extra_sugerido
            meses_com_extra = nper(taxa_juros_mensal, -parcela_com_extra, saldo_devedor)

            return (
                f"Análise da dívida '{nome_divida}':\n"
                f"Saldo devedor atual: R$ {saldo_devedor:,.2f}\n"
                f"Com a parcela atual de R$ {valor_parcela:,.2f}, faltam cerca de {meses_restantes:.1f} meses para quitar.\n"
                f"**Sugestão Proativa:** Se você puder pagar R$ {parcela_com_extra:,.2f} por mês (R$ {extra_sugerido:,.2f} a mais), "
                f"você quitaria a dívida em aproximadamente {meses_com_extra:.1f} meses, economizando juros."
            )
        except ValueError as e:
            return f"Erro ao analisar dívida '{nome_divida}'. Verifique se os valores na planilha (juros, parcelas) são números válidos. Detalhe: {e}"
        except Exception as e:
            return f"Erro inesperado ao analisar dívida '{nome_divida}': {e}"
