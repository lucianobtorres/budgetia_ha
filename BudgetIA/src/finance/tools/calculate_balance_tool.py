from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import CalcularSaldoTotalInput


class CalcularSaldoTotalTool(BaseTool):  # type: ignore[misc]
    name: str = "calcular_saldo_total"
    description: str = (
        "Calcula e retorna o saldo financeiro total (Receitas - Despesas) da Planilha Mestra. "
        "Use esta ferramenta quando o usuário perguntar sobre seu 'saldo', 'dinheiro disponível', 'balanço atual', etc."
    )
    args_schema: type[BaseModel] = CalcularSaldoTotalInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self) -> str:
        """
        Calcula o saldo chamando o método centralizado get_summary()
        do PlanilhaManager e formata a saída para o padrão BRL (R$ 4.200,00).
        """
        print(f"LOG: Ferramenta '{self.name}' foi chamada.")
        try:
            # Pedimos o resumo completo ao maestro
            resumo = self.planilha_manager.get_summary()

            # Pegamos apenas o valor do saldo que a ferramenta precisa
            saldo = resumo.get("saldo", 0.0)

            # --- INÍCIO DA CORREÇÃO DE FORMATO ---
            # 1. Formata no padrão "inglês" (ex: 4,200.00)
            saldo_str_en = f"{saldo:,.2f}"

            # 2. Converte para o padrão BRL (ex: 4.200,00)
            # Trocamos vírgula por "X" temporário, ponto por vírgula, "X" por ponto.
            saldo_str_br = (
                saldo_str_en.replace(",", "X").replace(".", ",").replace("X", ".")
            )

            return f"O saldo financeiro total atual é de R$ {saldo_str_br}."
            # --- FIM DA CORREÇÃO DE FORMATO ---

        except Exception as e:
            # Captura qualquer erro que possa ocorrer no cálculo
            return f"Erro ao calcular o saldo: {e}"
