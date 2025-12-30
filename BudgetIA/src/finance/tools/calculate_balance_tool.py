# src/finance/tools/calculate_balance_tool.py
from collections.abc import Callable  # Importar Callable

from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.schemas import CalcularSaldoTotalInput

from core.logger import get_logger

logger = get_logger("Tool_CalcBalance")


class CalcularSaldoTotalTool(BaseTool):  # type: ignore[misc]
    name: str = "calcular_saldo_total"
    description: str = (
        "Calcula e retorna o saldo financeiro total (Receitas - Despesas) da Planilha Mestra. "
        "Use esta ferramenta quando o usuário perguntar sobre seu 'saldo', 'dinheiro disponível', 'balanço atual', etc."
    )
    args_schema: type[BaseModel] = CalcularSaldoTotalInput

    # --- DIP: Depende de Callables ---
    def __init__(self, get_summary_func: Callable[[], dict[str, float]]) -> None:
        self.get_summary = get_summary_func

    # --- FIM DA MUDANÇA ---

    def run(self) -> str:
        """
        Calcula o saldo chamando a função injetada e formata a saída.
        """
        logger.info(f"Ferramenta '{self.name}' foi chamada.")
        try:
            # --- DIP: Chama a função injetada ---
            resumo = self.get_summary()
            saldo = resumo.get("saldo", 0.0)

            # Formatação BRL
            saldo_str_en = f"{saldo:,.2f}"
            saldo_str_br = (
                saldo_str_en.replace(",", "X").replace(".", ",").replace("X", ".")
            )

            return f"O saldo financeiro total atual é de R$ {saldo_str_br}."
        except Exception as e:
            return f"Erro ao calcular o saldo: {e}"
