# src/finance/tools/force_sync_tool.py

from typing import Any

from planilha_manager import PlanilhaManager
from pydantic.v1 import BaseModel

from core.base_tool import BaseTool


class ForceSyncTool(BaseTool):  # type: ignore[misc]
    """
    Ferramenta para forçar a invalidação do cache e recarregar
    os dados da Planilha Mestra (Google Drive/Excel).
    Use isso se o usuário mencionar que atualizou a planilha
    manualmente e os dados parecem desatualizados.
    """

    name: str = "forcar_sincronizacao_planilha"
    description: str = (
        "Força o sistema a limpar o cache e reler todos os dados da Planilha Mestra. "
        "Use APENAS se o usuário explicitamente pedir para 'sincronizar', 'recarregar', "
        "'atualizar' ou se ele disser que fez uma mudança 'por fora' do app."
    )
    args_schema: type[BaseModel] = None  # Não precisa de argumentos
    planilha_manager: PlanilhaManager

    def __init__(self, planilha_manager: PlanilhaManager, **kwargs: Any) -> None:
        super().__init__(planilha_manager=planilha_manager, **kwargs)

    def _run(self) -> str:
        """Executa a ferramenta."""
        try:
            self.planilha_manager.clear_cache()
            return "Ok, o cache foi limpo. Forcei uma sincronização com sua Planilha Mestra. Os dados agora estão 100% atualizados."
        except Exception as e:
            return f"Erro ao tentar forçar a sincronização: {e}"
