import datetime

from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import RegistrarInsightIAInput


class RegistrarInsightIATool(BaseTool):  # type: ignore[misc]
    name: str = "registrar_insight_ia"
    description: str = (
        "Registra um insight, alerta ou recomendação gerada pela IA na aba 'Consultoria da IA'. "
        "Use esta ferramenta para fornecer feedback proativo e educacional ao usuário sobre sua situação financeira."
    )
    args_schema: type[BaseModel] = RegistrarInsightIAInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(
        self,
        tipo_insight: str,
        titulo_insight: str,
        detalhes_recomendacao: str,
        status: str = "Novo",
    ) -> str:
        print(
            f"LOG: Ferramenta '{self.name}' chamada: Tipo='{tipo_insight}', Título='{titulo_insight}'"
        )
        data_insight = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.planilha_manager.adicionar_insight_ia(
                data_insight,
                tipo_insight,
                titulo_insight,
                detalhes_recomendacao,
                status,
            )
            return f"Insight de IA '{titulo_insight}' registrado com sucesso na aba 'Consultoria da IA'!"
        except Exception as e:
            return f"Erro ao registrar insight de IA: {e}"
