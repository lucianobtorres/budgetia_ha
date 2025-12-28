# src/finance/tools/analyze_adherence_tool.py
import json
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel

from config import ColunasTransacoes, NomesAbas, ValoresTipo
from core.base_tool import BaseTool
from finance.financial_rules import FinancialRules
from finance.schemas import AnalisarAdesaoInput


class AnalisarAdesaoFinanceiraTool(BaseTool):  # type: ignore[misc]
    name: str = "analisar_adesao_financeira"
    description: str = (
        "Analisa a distribuição da receita do usuário em relação a uma regra financeira específica (ex: 50/30/20, 20/10/60/10). "
        "Use esta ferramenta sempre que o usuário perguntar sobre a saúde geral do orçamento ou a adesão a uma regra."
    )
    args_schema: type[BaseModel] = AnalisarAdesaoInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        super().__init__()
        self.visualizar_dados = view_data_func

    # --- FIM DA MUDANÇA ---

    def run(self, rule_name: str) -> str:
        print(
            f"LOG: Ferramenta '{self.name}' chamada: Analisando a regra '{rule_name}'."
        )

        regras_alvo = FinancialRules.get_target_percentages(rule_name)
        if not regras_alvo:
            return f"Erro: A regra '{rule_name}' não é reconhecida. As regras disponíveis são: {', '.join(FinancialRules.get_available_rules())}"

        # --- DIP: Chama a função injetada ---
        df = self.visualizar_dados(sheet_name=NomesAbas.TRANSACOES)
        if df.empty:
            return "Não há dados na planilha para analisar a distribuição da receita."

        total_receita = df[df[ColunasTransacoes.TIPO] == ValoresTipo.RECEITA][
            ColunasTransacoes.VALOR
        ].sum()
        despesas_por_cat = (
            df[df[ColunasTransacoes.TIPO] == ValoresTipo.DESPESA]
            .groupby(ColunasTransacoes.CATEGORIA)[ColunasTransacoes.VALOR]
            .sum()
        )

        if total_receita <= 0:
            return "Não foi registrada receita para analisar a distribuição."

        mapping = FinancialRules.get_category_mapping()
        grupos_calculados: dict[str, float] = {
            grupo: 0.0 for grupo in regras_alvo.keys()
        }

        for cat_regra, categorias_planilha in mapping.items():
            if cat_regra in grupos_calculados:
                gastos_do_grupo = despesas_por_cat[
                    despesas_por_cat.index.astype(str)
                    .str.lower()
                    .isin([c.lower() for c in categorias_planilha])
                ].sum()
                grupos_calculados[cat_regra] = float(gastos_do_grupo)

        total_gasto = sum(grupos_calculados.values())
        destinado_a_investimento = total_receita - total_gasto

        if "INVESTIMENTO_DIVIDA" in regras_alvo:
            investimento_e_divida = destinado_a_investimento + grupos_calculados.get(
                "DIVIDAS_EDUCACAO", 0.0
            )
            grupos_calculados["INVESTIMENTO_DIVIDA"] = investimento_e_divida
            grupos_calculados.pop("DIVIDAS_EDUCACAO", None)
            grupos_calculados.pop("INVESTIMENTO_POUPANCA", None)
        elif "INVESTIMENTO_POUPANCA" in regras_alvo:
            # Garante que o que sobrou seja considerado investimento
            grupos_calculados["INVESTIMENTO_POUPANCA"] += destinado_a_investimento

        resumo_adesao = {}
        for grupo, alvo_pct in regras_alvo.items():
            valor_real = grupos_calculados.get(grupo, 0.0)

            # Garante que o valor real não seja negativo (acontece se gastou mais que ganhou)
            valor_real = max(valor_real, 0.0)

            pct_real = (valor_real / total_receita) * 100 if total_receita > 0 else 0.0
            alvo_pct_100 = alvo_pct * 100

            status = "Atingido"
            if pct_real > alvo_pct_100:
                status = "Acima"
            elif pct_real < (alvo_pct_100 * 0.9):  # 90% da meta
                status = "Abaixo"

            resumo_adesao[grupo] = {
                "Alvo_Pct": alvo_pct_100,
                "Real_Pct": pct_real,
                "Valor_Real": valor_real,
                "Alvo_Valor": total_receita * alvo_pct,
                "Status": status,
            }

        return f"Análise da Regra '{rule_name}':\n{json.dumps(resumo_adesao, indent=2)}"
