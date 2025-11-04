# Em: src/finance/tools/collect_user_profile_tool.py
# (Substitua todo o conteúdo deste arquivo)

from typing import Any

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager
from finance.schemas import ColetarPerfilUsuarioInput  # Importa o schema CORRETO


class ColetarPerfilUsuarioTool(BaseTool):  # type: ignore[misc]
    """
    Ferramenta para salvar UMA informação (campo/valor) na aba 'Perfil Financeiro'.
    """

    name: str = "coletar_perfil_usuario"
    description: str = (
        "Salva ou atualiza UMA informação específica (um par campo/valor) na aba 'Perfil Financeiro' "
        "do usuário, como 'Renda Mensal Média' ou 'Principal Objetivo'. "
        "Use esta ferramenta sempre que o usuário fornecer um dado de perfil durante o onboarding."
    )
    args_schema = ColetarPerfilUsuarioInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        super().__init__()
        self.planilha_manager = planilha_manager

    def run(self, campo: str, valor: Any) -> str:
        """
        Executa a ferramenta para salvar o dado do perfil usando o PlanilhaManager.
        """
        print(
            f"LOG: Ferramenta '{self.name}' chamada para salvar Campo='{campo}', Valor='{valor}'"
        )

        if not self.planilha_manager:
            return "Erro: PlanilhaManager não inicializado."

        try:
            # Chama o método correto do PlanilhaManager
            mensagem = self.planilha_manager.salvar_dado_perfil(
                campo=campo, valor=valor
            )
            return str(mensagem)
        except Exception as e:
            print(f"ERRO DE EXECUÇÃO NA TOOL DE PERFIL: {e}")
            return f"Erro ao salvar dado do perfil: {e}"
