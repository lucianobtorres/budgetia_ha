# src/finance/tools/collect_user_profile_tool.py
from collections.abc import Callable  # Importar Callable
from typing import Any

from core.base_tool import BaseTool
from finance.schemas import ColetarPerfilUsuarioInput


class ColetarPerfilUsuarioTool(BaseTool):  # type: ignore[misc]
    """
    Ferramenta para salvar UMA informação (campo/valor) na aba 'Perfil Financeiro'.
    """

    name: str = "coletar_perfil_usuario"
    description: str = (
        "Salva ou atualiza UMA informação específica (um par campo/valor) na aba 'Perfil Financeiro' "
        "do usuário, como 'Renda Mensal Média' ou 'Principal Objetivo'."
    )
    args_schema = ColetarPerfilUsuarioInput

    # --- DIP: Depende de Callables ---
    def __init__(self, save_profile_func: Callable[..., str]) -> None:
        super().__init__()
        self.salvar_dado_perfil = save_profile_func

    # --- FIM DA MUDANÇA ---

    def run(self, campo: str, valor: Any) -> str:
        """
        Executa a ferramenta para salvar o dado do perfil.
        """
        print(
            f"LOG: Ferramenta '{self.name}' chamada para salvar Campo='{campo}', Valor='{valor}'"
        )

        try:
            # --- DIP: Chama a função injetada ---
            # (A função salvar_dado_perfil já salva automaticamente)
            mensagem = self.salvar_dado_perfil(campo=campo, valor=valor)
            return str(mensagem)
        except Exception as e:
            print(f"ERRO DE EXECUÇÃO NA TOOL DE PERFIL: {e}")
            return f"Erro ao salvar dado do perfil: {e}"
