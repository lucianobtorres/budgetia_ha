from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager

from ..schemas import VerificarStatusOrcamentoInput


class VerificarStatusOrcamentoTool(BaseTool):  # type: ignore[misc]
    name: str = "verificar_status_orcamento"
    description: str = (
        "Verifica o status atual de um orçamento específico por categoria ou de todos os orçamentos ativos. "
        "Retorna informações sobre o valor orçado, gasto atual, porcentagem gasta e status. "
        "Use para 'Como está meu orçamento de alimentação?', 'Estou estourando meu orçamento?', 'Me mostre o status de todos os orçamentos'."
    )
    args_schema: type[BaseModel] = VerificarStatusOrcamentoInput

    def __init__(self, planilha_manager: PlanilhaManager) -> None:
        self.planilha_manager = planilha_manager

    def run(self, categoria: str | None = None) -> str:
        print(f"LOG: Ferramenta '{self.name}' chamada para Categoria={categoria}.")
        self.planilha_manager._calcular_e_atualizar_gastos_orcamentos()  # Garante que os valores em memória estejam atualizados
        orcamentos_df = self.planilha_manager.visualizar_dados(
            aba_nome="Meus Orçamentos"
        )

        if orcamentos_df.empty:
            return "Não há orçamentos definidos na planilha."

        if categoria:
            orcamento_encontrado = orcamentos_df[
                orcamentos_df["Categoria"].astype(str).str.lower() == categoria.lower()
            ]
            if orcamento_encontrado.empty:
                return f"Orçamento para a categoria '{categoria}' não encontrado."

            # Retornar apenas o primeiro encontrado se houver duplicatas por algum motivo
            orc = orcamento_encontrado.iloc[0]
            return (
                f"Status do orçamento para '{orc['Categoria']}' ({orc['Período Orçamento']}):\n"
                f"Orçado: R$ {orc['Valor Limite Mensal']:,.2f}\n"
                f"Gasto Atual: R$ {orc['Valor Gasto Atual']:,.2f}\n"
                f"Porcentagem Gasta: {orc['Porcentagem Gasta (%)']:.1f}%\n"
                f"Status: {orc['Status Orçamento']}. "
                f"Última atualização: {orc['Última Atualização Orçamento']}."
            )
        else:
            # Retorna todos os orçamentos de forma resumida
            resumo_orcamentos = orcamentos_df[
                [
                    "Categoria",
                    "Valor Limite Mensal",
                    "Valor Gasto Atual",
                    "Porcentagem Gasta (%)",
                    "Status Orçamento",
                ]
            ]
            return f"Resumo de todos os orçamentos:\n{resumo_orcamentos.to_markdown(index=False)}"
