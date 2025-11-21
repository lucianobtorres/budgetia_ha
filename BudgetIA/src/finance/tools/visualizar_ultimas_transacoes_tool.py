# src/finance/tools/visualizar_ultimas_transacoes_tool.py
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel, Field
from tabulate import tabulate

from config import ColunasTransacoes, NomesAbas
from core.base_tool import BaseTool


class VisualizarUltimasTransacoesInput(BaseModel):
    n: int = Field(
        default=5, description="O número de últimas transações a serem visualizadas."
    )
    tipo: str | None = Field(
        default=None,
        description="Filtro opcional pelo tipo de transação: 'Receita' ou 'Despesa'.",
    )


class VisualizarUltimasTransacoesTool(BaseTool):  # type: ignore[misc]
    name: str = "visualizar_ultimas_transacoes"
    description: str = (
        "Visualiza as 'n' últimas transações registradas, ordenadas por data. Pode ser filtrado por tipo ('Receita' ou 'Despesa')."
    )
    args_schema = VisualizarUltimasTransacoesInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self, n: int = 5, tipo: str | None = None) -> str:
        try:
            # --- DIP: Chama a função injetada ---
            df = self.visualizar_dados(NomesAbas.TRANSACOES).copy()
            if df.empty:
                return "Não há transações registradas na planilha."

            # Tenta converter 'Data' para datetime
            if ColunasTransacoes.DATA in df.columns:
                df[ColunasTransacoes.DATA] = pd.to_datetime(
                    df[ColunasTransacoes.DATA], errors="coerce"
                )
                df.dropna(subset=[ColunasTransacoes.DATA], inplace=True)
            else:
                return "Erro: A aba de transações não possui uma coluna 'Data'."

            if tipo:
                df_filtrado = df[
                    df[ColunasTransacoes.TIPO].astype(str).str.lower() == tipo.lower()
                ]
            else:
                df_filtrado = df

            if df_filtrado.empty:
                tipo_str = f" do tipo '{tipo}'" if tipo else ""
                return f"Não foram encontradas transações{tipo_str}."

            ultimas_transacoes = df_filtrado.sort_values(
                by=ColunasTransacoes.DATA, ascending=False
            ).head(n)

            if ultimas_transacoes.empty:
                return "Não há transações para mostrar com os filtros aplicados."

            headers = [
                ColunasTransacoes.DATA,
                ColunasTransacoes.TIPO,
                ColunasTransacoes.CATEGORIA,
                ColunasTransacoes.DESCRICAO,
                ColunasTransacoes.VALOR,
            ]
            # Filtra colunas que realmente existem no DF
            colunas_para_mostrar = [
                col for col in headers if col in ultimas_transacoes.columns
            ]

            tabela = tabulate(
                ultimas_transacoes[colunas_para_mostrar],
                headers="keys",
                tablefmt="pipe",
                showindex=False,
            )

            tipo_str_retorno = f" do tipo '{tipo}'" if tipo else ""
            return f"Suas {len(ultimas_transacoes)} últimas transações{tipo_str_retorno}:\n{tabela}"

        except Exception as e:
            return f"Ocorreu um erro ao visualizar as últimas transações: {e}"
