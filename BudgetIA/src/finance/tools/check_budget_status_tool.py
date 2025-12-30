# src/finance/tools/check_budget_status_tool.py
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel

from config import ColunasOrcamentos, NomesAbas
from core.base_tool import BaseTool
from finance.schemas import VerificarStatusOrcamentoInput

from core.logger import get_logger

logger = get_logger("Tool_CheckBudget")


class VerificarStatusOrcamentoTool(BaseTool):  # type: ignore[misc]
    name: str = "verificar_status_orcamento"
    description: str = (
        "Verifica o status atual de um orçamento específico por categoria ou de todos os orçamentos ativos. "
        "Retorna informações sobre o valor orçado, gasto atual, porcentagem gasta e status."
    )
    args_schema: type[BaseModel] = VerificarStatusOrcamentoInput

    # --- DIP: Depende de Callables ---
    def __init__(
        self,
        recalculate_budgets_func: Callable[[], None],
        view_data_func: Callable[..., pd.DataFrame],
    ) -> None:
        self.recalculate_budgets = recalculate_budgets_func
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self, categoria: str | None = None) -> str:
        logger.info(f"Ferramenta '{self.name}' chamada para Categoria={categoria}.")

        try:
            # --- DIP: Chama as funções injetadas ---
            # 1. Garante que os valores estão atualizados ANTES de visualizar
            self.recalculate_budgets()

            # 2. Visualiza os dados atualizados
            orcamentos_df = self.visualizar_dados(aba_nome=NomesAbas.ORCAMENTOS)
            # --- Fim das chamadas ---

            if orcamentos_df.empty:
                return "Não há orçamentos definidos na planilha."

            if categoria:
                orcamento_encontrado = orcamentos_df[
                    orcamentos_df[ColunasOrcamentos.CATEGORIA].astype(str).str.lower()
                    == categoria.lower()
                ]
                if orcamento_encontrado.empty:
                    return f"Orçamento para a categoria '{categoria}' não encontrado."

                orc = orcamento_encontrado.iloc[0].to_dict()

                # Formatação segura
                limite_f = f"{orc.get(ColunasOrcamentos.LIMITE, 0):,.2f}"
                gasto_f = f"{orc.get(ColunasOrcamentos.GASTO, 0):,.2f}"
                pct_f = f"{orc.get(ColunasOrcamentos.PERCENTUAL, 0):.1f}"

                return (
                    f"Status do orçamento para '{orc.get('Categoria', 'N/A')}' ({orc.get('Período Orçamento', 'N/A')}):\n"
                    f"Orçado: R$ {limite_f.replace(',', 'X').replace('.', ',').replace('X', '.')}\n"
                    f"Gasto Atual: R$ {gasto_f.replace(',', 'X').replace('.', ',').replace('X', '.')}\n"
                    f"Porcentagem Gasta: {pct_f}%\n"
                    f"Status: {orc.get('Status Orçamento', 'N/A')}. "
                    f"Última atualização: {orc.get(ColunasOrcamentos.ATUALIZACAO, 'N/A')}."
                )
            else:
                resumo_orcamentos = orcamentos_df[
                    [
                        ColunasOrcamentos.CATEGORIA,
                        ColunasOrcamentos.LIMITE,
                        ColunasOrcamentos.GASTO,
                        ColunasOrcamentos.PERCENTUAL,
                        ColunasOrcamentos.STATUS,
                    ]
                ]
                return f"Resumo de todos os orçamentos:\n{resumo_orcamentos.to_markdown(index=False)}"
        except Exception as e:
            return f"Erro ao verificar orçamentos: {e}"
