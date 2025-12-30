# src/finance/tools/add_debt_tool.py
from collections.abc import Callable  # Importar Callable

from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.schemas import AdicionarDividaInput

from core.logger import get_logger

logger = get_logger("Tool_AddDebt")


class AdicionarDividaTool(BaseTool):  # type: ignore[misc]
    name: str = "adicionar_divida"
    description: str = (
        "Adiciona uma nova dívida à aba 'Minhas Dívidas' da Planilha Mestra. "
        "Calcula o saldo devedor atual com base nas parcelas pagas."
    )
    args_schema: type[BaseModel] = AdicionarDividaInput

    # --- DIP: Depende de Callables ---
    def __init__(
        self,
        add_debt_func: Callable[..., str],
        save_func: Callable[[], None],
    ) -> None:
        self.adicionar_ou_atualizar_divida = add_debt_func
        self.save = save_func

    # --- FIM DA MUDANÇA ---

    def run(
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
        logger.info(f"Ferramenta '{self.name}' chamada para {nome_divida}.")
        try:
            # --- DIP: Chama as funções injetadas ---
            mensagem = self.adicionar_ou_atualizar_divida(
                nome_divida,
                valor_original,
                taxa_juros_mensal,
                parcelas_totais,
                valor_parcela,
                parcelas_pagas,
                data_proximo_pgto,
                observacoes,
            )
            self.save()  # Salva a dívida
            return str(mensagem)
        except Exception as e:
            return f"Erro ao adicionar dívida: {e}"
