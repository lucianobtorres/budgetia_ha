# src/finance/tools/add_transaction_tool.py
import datetime
from typing import Callable, Any  # Importar Callable

from core.base_tool import BaseTool
from finance.schemas import AddTransactionInput

from core.logger import get_logger

logger = get_logger("Tool_AddTransaction")


class AddTransactionTool(BaseTool):  # type: ignore[misc]
    name: str = "adicionar_transacao"
    description: str = "Adiciona uma nova transação (receita ou despesa)."
    args_schema = AddTransactionInput

    # --- DIP: Depende de Callables (funções), não de uma classe concreta ---
    def __init__(
        self,
        add_transaction_func: Callable[..., None],
        save_func: Callable[[], None],
        get_summary_func: Callable[[], dict[str, float]],
        recalculate_budgets_func: Callable[[], Any],
    ) -> None:
        self.adicionar_registro = add_transaction_func
        self.save = save_func
        self.get_summary = get_summary_func
        self.recalculate_budgets_func = recalculate_budgets_func

    # --- FIM DA MUDANÇA ---

    def run(
        self,
        tipo: str,
        categoria: str,
        descricao: str,
        valor: float,
        status: str = "Concluído",
        data: str | None = None,
    ) -> str:
        # Lógica de inteligência da ferramenta (processamento de data)
        data_final: str
        hoje = datetime.date.today()

        if data is None or data.lower() == "hoje":
            data_final = hoje.strftime("%Y-%m-%d")
        elif data.lower() == "ontem":
            ontem = hoje - datetime.timedelta(days=1)
            data_final = ontem.strftime("%Y-%m-%d")
        elif data.lower() == "anteontem":
            anteontem = hoje - datetime.timedelta(days=2)
            data_final = anteontem.strftime("%Y-%m-%d")
        else:
            data_final = data

        try:
            # --- DIP: Chama as funções injetadas ---
            self.adicionar_registro(
                data=data_final,
                tipo=tipo,
                categoria=categoria,
                descricao=descricao,
                valor=valor,
                status=status,
            )
            self.save()  # Salva a transação

            logger.info("Transação adicionada. Acionando recálculo de orçamentos...")
            self.recalculate_budgets_func()

            resumo_atual = self.get_summary()
            # --- Fim das chamadas injetadas ---

            saldo_final = resumo_atual.get("saldo", 0.0)

            # Formatação BRL
            valor_str_en = f"{valor:,.2f}"
            valor_str_br = (
                valor_str_en.replace(",", "X").replace(".", ",").replace("X", ".")
            )
            saldo_str_en = f"{saldo_final:,.2f}"
            saldo_str_br = (
                saldo_str_en.replace(",", "X").replace(".", ",").replace("X", ".")
            )

            return (
                f"Transação '{descricao}' (Categoria: {categoria}) no valor de R$ {valor_str_br} "
                f"adicionada com sucesso em {data_final}. O novo saldo é R$ {saldo_str_br}."
            )
        except Exception as e:
            return f"Ocorreu um erro ao adicionar a transação: {e}"
