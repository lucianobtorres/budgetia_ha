# src/finance/tools/register_ai_insight_tool.py
import datetime
from collections.abc import Callable  # Importar Callable

from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.schemas import RegistrarInsightIAInput

from core.logger import get_logger

logger = get_logger("Tool_RegInsight")


class RegistrarInsightIATool(BaseTool):  # type: ignore[misc]
    name: str = "registrar_insight_ia"
    description: str = (
        "Registra um insight, alerta ou recomendação gerada pela IA na aba 'Consultoria da IA'. "
        "Use esta ferramenta para fornecer feedback proativo e educacional ao usuário."
    )
    args_schema: type[BaseModel] = RegistrarInsightIAInput

    # --- DIP: Depende de Callables ---
    def __init__(self, register_insight_func: Callable[..., None]) -> None:
        self.adicionar_insight_ia = register_insight_func

    # --- FIM DA MUDANÇA ---

    def run(
        self,
        tipo_insight: str,
        titulo_insight: str,
        detalhes_recomendacao: str,
        status: str = "Novo",
    ) -> str:
        logger.info(
            f"Ferramenta '{self.name}' chamada: Tipo='{tipo_insight}', Título='{titulo_insight}'"
        )
        data_insight = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # --- DIP: Chama a função injetada ---
            self.adicionar_insight_ia(
                data_insight,
                tipo_insight,
                titulo_insight,
                detalhes_recomendacao,
                status,
            )
            # Esta ferramenta não precisa de 'save', pois a lógica
            # de insights deve salvar quando apropriado (ou o agente salva no final).

            return f"Insight de IA '{titulo_insight}' registrado com sucesso na aba 'Consultoria da IA'!"
        except Exception as e:
            return f"Erro ao registrar insight de IA: {e}"
