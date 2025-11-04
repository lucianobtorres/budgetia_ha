from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import ExtrairTransacoesDoTextoInput


class ExtrairTransacoesDoTextoTool(BaseTool):  # type: ignore[misc]
    name: str = "extrair_transacoes_do_texto"
    description: str = (
        "Ferramenta auxiliar para analisar uma string de texto livre do usuário e extrair informações de transações financeiras "
        "(tipo, categoria, descrição, valor, data, status). "
        "Use esta ferramenta QUANDO o usuário fornecer múltiplas transações ou transações em formato livre que precisam ser estruturadas "
        "antes de serem adicionadas à planilha. "
        "Após extrair, o agente DEVE usar a ferramenta 'adicionar_transacao' para cada transação extraída."
        "A saída desta ferramenta é o texto fornecido pelo usuário, para que o AGENTE possa então extrair os parâmetros para a ferramenta 'adicionar_transacao'."
    )
    args_schema: type[BaseModel] = ExtrairTransacoesDoTextoInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self, texto_usuario: str) -> str:
        print(f"LOG: Ferramenta '{self.name}' chamada com texto: '{texto_usuario}'")
        # Esta ferramenta, por si só, não tem a inteligência para fazer a extração.
        # A inteligência de extração e categorização acontecerá no raciocínio do agente (LLM),
        # que usará o contexto da chamada desta ferramenta e as instruções no SystemMessage para entender
        # o que foi dito e, em seguida, chamar 'adicionar_transacao' para cada item.
        # Por isso, ela simplesmente retorna o texto de volta para o agente.
        return "Texto para extração processado. Agora use isso para preencher 'adicionar_transacao'."
