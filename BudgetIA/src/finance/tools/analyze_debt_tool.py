from numpy_financial import ipmt, nper
from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import AnalisarDividaInput


class AnalisarDividaTool(BaseTool):  # type: ignore[misc]
    name: str = "analisar_divida"
    description: str = (
        "Analisa uma dívida específica e sugere estratégias de quitação. "
        "Calcula o saldo devedor atual e projeta o tempo para quitação. "
        "Use para 'Qual a melhor forma de pagar a minha dívida do carro?', 'Me dê uma análise da minha dívida de cartão'."
    )
    args_schema: type[BaseModel] = AnalisarDividaInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self, nome_divida: str) -> str:
        print(
            f"LOG: Ferramenta '{self.name}' chamada para analisar dívida: {nome_divida}."
        )

        df = self.planilha_manager.visualizar_dados(aba_nome="Minhas Dívidas")
        if df.empty:
            return (
                "A aba de dívidas está vazia. Nenhuma dívida encontrada para análise."
            )

        divida_encontrada = df[df["Nome da Dívida"].str.lower() == nome_divida.lower()]

        if divida_encontrada.empty:
            return f"Dívida '{nome_divida}' não encontrada na planilha."

        divida = divida_encontrada.iloc[0]

        saldo_devedor = divida["Saldo Devedor Atual"]
        taxa_juros_mensal = divida["Taxa Juros Mensal (%)"] / 100
        valor_parcela = divida["Valor Parcela"]

        if saldo_devedor <= 0:
            return f"A dívida '{nome_divida}' já está quitada."

        # Análise básica
        if valor_parcela <= ipmt(
            taxa_juros_mensal,
            1,
            nper(taxa_juros_mensal, valor_parcela, saldo_devedor),
            saldo_devedor,
        ):
            return "AVISO: A parcela da sua dívida é insuficiente para cobrir os juros. Isso pode fazer sua dívida crescer. Recomendo negociar com o credor."

        # Projeta o número de meses para quitação
        meses_restantes = nper(taxa_juros_mensal, -valor_parcela, saldo_devedor)

        # Sugestão de amortização (pagar um extra)
        parcela_com_extra = valor_parcela + (
            saldo_devedor * 0.05
        )  # Ex: pagar 5% a mais
        meses_com_extra = nper(taxa_juros_mensal, -parcela_com_extra, saldo_devedor)

        return (
            f"Análise da dívida '{nome_divida}':\n"
            f"Saldo devedor atual: R$ {saldo_devedor:,.2f}\n"
            f"Com a parcela atual de R$ {valor_parcela:,.2f}, faltam cerca de {meses_restantes:.1f} meses para quitar.\n"
            f"**Sugestão Proativa:** Se você puder pagar R$ {parcela_com_extra:,.2f} por mês (R$ {saldo_devedor * 0.05:,.2f} extra), "
            f"você quitaria a dívida em aproximadamente {meses_com_extra:.1f} meses, economizando juros."
        )
