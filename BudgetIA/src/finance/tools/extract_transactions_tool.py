# src/finance/tools/extract_transactions_tool.py
from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.schemas import ExtrairTransacoesDoTextoInput


class ExtrairTransacoesDoTextoTool(BaseTool):  # type: ignore[misc]
    name: str = "extrair_transacoes_do_texto"
    description: str = (
        "Ferramenta auxiliar para analisar uma string de texto livre do usuário e extrair informações de transações financeiras. "
        "Use esta ferramenta QUANDO o usuário fornecer múltiplas transações ou transações em formato livre que precisam ser estruturadas. "
        "Após extrair, o agente DEVE usar a ferramenta 'adicionar_transacao' para cada transação extraída."
    )
    args_schema: type[BaseModel] = ExtrairTransacoesDoTextoInput

    # --- DIP: Esta ferramenta não tem dependências ---
    def __init__(self) -> None:
        pass  # Não precisa de nenhuma função

    # --- FIM DA MUDANÇA ---

    def run(self, texto_usuario: str) -> str:
        print(f"LOG: Ferramenta '{self.name}' chamada com texto: '{texto_usuario}'")
        # Esta ferramenta é um "placeholder" para o LLM.
        # Ela apenas confirma que o LLM deve focar neste texto.
        # A lógica de extração real é feita pelo LLM em seguida.
        return (
            "Texto para extração recebido. "
            "Agora, use 'adicionar_transacao' para cada item identificado."
        )
