# src/finance/tools/add_transaction_tool.py
import datetime

from core.base_tool import BaseTool  # Importa a classe pai limpa
from finance.planilha_manager import PlanilhaManager
from finance.schemas import AddTransactionInput


class AddTransactionTool(BaseTool):  # type: ignore[misc]
    name: str = "adicionar_transacao"
    description: str = "Adiciona uma nova transação (receita ou despesa)."
    args_schema = AddTransactionInput

    # O __init__ é responsabilidade da classe filha
    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    # Em src/finance/tools/add_transaction_tool.py
    # Não esqueça de adicionar 'import datetime' no topo do arquivo.
    def run(
        self,
        tipo: str,
        categoria: str,
        descricao: str,
        valor: float,
        status: str = "Concluído",
        data: str | None = None,
    ) -> str:
        if not self.planilha_manager:
            return "Erro: O PlanilhaManager não foi inicializado corretamente."

        # --- NOVA LÓGICA DE INTELIGÊNCIA DA FERRAMENTA ---
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
            # Se não for uma palavra-chave, assume que é uma data no formato correto
            data_final = data
        # --- FIM DA NOVA LÓGICA ---

        try:
            self.planilha_manager.adicionar_registro(
                data=data_final,  # Usa a data processada
                tipo=tipo,
                categoria=categoria,
                descricao=descricao,
                valor=valor,
                status=status,
            )
            self.planilha_manager.save()

            resumo_atual = self.planilha_manager.get_summary()
            saldo_final = resumo_atual.get("saldo", 0.0)

            valor_str_en = f"{valor:,.2f}"
            valor_str_br = (
                valor_str_en.replace(",", "X").replace(".", ",").replace("X", ".")
            )

            return (
                f"Transação '{descricao}' (Categoria: {categoria}) no valor de R$ {valor_str_br} "
                f"adicionada com sucesso em {data_final}. O novo saldo é R$ {saldo_final:.2f}."
            )
        except Exception as e:
            return f"Ocorreu um erro ao adicionar a transação: {e}"
