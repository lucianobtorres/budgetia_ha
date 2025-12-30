# src/finance/tools/generate_monthly_summary_tool.py
import json
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel

from config import ColunasTransacoes, NomesAbas, SummaryKeys, ValoresTipo
from core.base_tool import BaseTool
from finance.schemas import GerarResumoMensalInput

from core.logger import get_logger

logger = get_logger("Tool_GenMthlySummary")


class GerarResumoMensalTool(BaseTool):  # type: ignore[misc]
    name: str = "gerar_resumo_mensal"
    description: str = (
        "Gera um resumo detalhado de receitas, despesas e saldo para um mês/ano específico "
        "ou para todos os meses disponíveis se nenhum for especificado."
    )
    args_schema: type[BaseModel] = GerarResumoMensalInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self, ano: int | None = None, mes: int | None = None) -> str:
        logger.info(f"Ferramenta '{self.name}' chamada para Ano={ano}, Mês={mes}.")

        # --- DIP: Chama a função injetada ---
        df = self.visualizar_dados(sheet_name=NomesAbas.TRANSACOES)
        if df.empty:
            return "Não há dados na planilha para gerar um resumo mensal."

        try:
            df[ColunasTransacoes.DATA] = pd.to_datetime(
                df[ColunasTransacoes.DATA], errors="coerce"
            )
            df.dropna(
                subset=[ColunasTransacoes.DATA], inplace=True
            )  # Ignora dados sem data
            df["AnoMes"] = df[ColunasTransacoes.DATA].dt.to_period("M")
        except Exception as e:
            return f"Erro ao processar datas da planilha: {e}"

        if ano and mes:
            periodo_filtro = pd.Period(year=ano, month=mes, freq="M")
            df_filtrado = df[df["AnoMes"] == periodo_filtro]
            if df_filtrado.empty:
                return f"Não há transações para o mês {mes}/{ano}."
            resumo_por_periodo = self._calcular_resumo_para_df(df_filtrado)
            return (
                f"Resumo para {mes}/{ano}:\n{json.dumps(resumo_por_periodo, indent=2)}"
            )
        elif ano:
            df_filtrado = df[df[ColunasTransacoes.DATA].dt.year == ano]
            if df_filtrado.empty:
                return f"Não há transações para o ano {ano}."

            resumos = {}
            for periodo, grupo in df_filtrado.groupby("AnoMes"):
                resumos[str(periodo)] = self._calcular_resumo_para_df(grupo)

            if not resumos:
                return f"Nenhum dado encontrado para o ano {ano}."
            return f"Resumo para o ano {ano}:\n{json.dumps(resumos, indent=2)}"
        else:  # Resumo geral por mês
            resumos = {}
            for periodo, grupo in df.groupby("AnoMes"):
                resumos[str(periodo)] = self._calcular_resumo_para_df(grupo)

            if not resumos:
                return "Não há dados suficientes para um resumo geral."
            return f"Resumo geral por mês:\n{json.dumps(resumos, indent=2)}"

    def _calcular_resumo_para_df(self, df_periodo: pd.DataFrame) -> dict[str, float]:
        """Função auxiliar para calcular resumo para um DataFrame de um período."""
        receitas = df_periodo[
            df_periodo[ColunasTransacoes.TIPO] == ValoresTipo.RECEITA
        ][ColunasTransacoes.VALOR].sum()
        despesas = df_periodo[
            df_periodo[ColunasTransacoes.TIPO] == ValoresTipo.DESPESA
        ][ColunasTransacoes.VALOR].sum()
        saldo = receitas - despesas
        return {
            SummaryKeys.RECEITAS: float(receitas),  # Chave correta
            SummaryKeys.DESPESAS: float(despesas),  # Chave correta
            SummaryKeys.SALDO: float(saldo),
        }
