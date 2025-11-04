from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import AdicionarDividaInput


class AdicionarDividaTool(BaseTool):  # type: ignore[misc]
    name: str = "adicionar_divida"
    description: str = (
        "Adiciona uma nova dívida à aba 'Minhas Dívidas' da Planilha Mestra. "
        "Útil para o usuário registrar empréstimos, financiamentos, etc. "
        "Calcula o saldo devedor atual com base nas parcelas pagas. "
        "Parâmetros: "
        "- nome_divida: O nome da dívida ou credor. "
        "- valor_original: O valor total original da dívida. "
        "- taxa_juros_mensal: A taxa de juros mensal em porcentagem. "
        "- parcelas_totais: O número total de parcelas. "
        "- valor_parcela: O valor de cada parcela. "
        "- parcelas_pagas: O número de parcelas já pagas (padrão 0). "
        "- data_proximo_pgto: Data do próximo pagamento (opcional). "
        "Retorna uma string de confirmação."
    )
    args_schema: type[BaseModel] = AdicionarDividaInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

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
        print(f"LOG: Ferramenta '{self.name}' chamada para {nome_divida}.")
        try:
            mensagem = self.planilha_manager.adicionar_ou_atualizar_divida(
                nome_divida,
                valor_original,
                taxa_juros_mensal,
                parcelas_totais,
                valor_parcela,
                parcelas_pagas,
                data_proximo_pgto,
                observacoes,
            )
            self.planilha_manager.save()
            return str(mensagem)
        except Exception as e:
            return f"Erro ao adicionar dívida: {e}"
