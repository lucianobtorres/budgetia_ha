# src/finance/tools/analyze_adherence_tool.py
import json

from pydantic import BaseModel, Field

from core.base_tool import BaseTool
from finance.financial_rules import FinancialRules
from finance.planilha_manager import PlanilhaManager


class AnalisarAdesaoInput(BaseModel):
    rule_name: str = Field(
        description=f"O nome da regra de ouro financeira a ser analisada. Escolha entre: {', '.join(FinancialRules.get_available_rules())}"
    )


class AnalisarAdesaoFinanceiraTool(BaseTool):
    name: str = "analisar_adesao_financeira"
    description: str = (
        "Analisa a distribuição da receita do usuário em relação a uma regra financeira específica (ex: 50/30/20, 20/10/60/10). "
        "Usa as categorias da planilha e as compara com os objetivos da regra. "
        "Use esta ferramenta sempre que o usuário perguntar sobre a saúde geral do orçamento ou a adesão a uma regra."
    )
    args_schema: type[BaseModel] = AnalisarAdesaoInput

    def __init__(self, planilha_manager: PlanilhaManager):
        super().__init__()
        self.planilha_manager = planilha_manager

    def run(self, rule_name: str) -> str:
        print(
            f"LOG: Ferramenta '{self.name}' chamada: Analisando a regra '{rule_name}'."
        )

        regras_alvo = FinancialRules.get_target_percentages(rule_name)
        if not regras_alvo:
            return f"Erro: A regra '{rule_name}' não é reconhecida. As regras disponíveis são: {', '.join(FinancialRules.get_available_rules())}"

        df = self.planilha_manager.visualizar_dados(aba_nome="Visão Geral e Transações")
        if df.empty:
            return "Não há dados na planilha para analisar a distribuição da receita."

        total_receita = df[df["Tipo (Receita/Despesa)"] == "Receita"]["Valor"].sum()
        despesas_por_cat = (
            df[df["Tipo (Receita/Despesa)"] == "Despesa"]
            .groupby("Categoria")["Valor"]
            .sum()
        )

        if total_receita <= 0:
            return "Não foi registrada receita para analisar a distribuição."

        # Mapear as categorias do usuário para os grupos da regra
        mapping = FinancialRules.get_category_mapping()
        grupos_calculados: Dict[str, float] = {
            grupo: 0.0 for grupo in regras_alvo.keys()
        }

        # Lógica para mapear os gastos do usuário aos grupos
        for cat_regra, categorias_planilha in mapping.items():
            if cat_regra in grupos_calculados:
                # Filtra despesas_por_cat pelas categorias da planilha que pertencem a este grupo
                gastos_do_grupo = despesas_por_cat[
                    despesas_por_cat.index.str.lower().isin(
                        [c.lower() for c in categorias_planilha]
                    )
                ].sum()
                grupos_calculados[cat_regra] = float(gastos_do_grupo)

        # O remanescente da receita que não foi gasto (idealmente, Investimento)
        total_gasto = sum(grupos_calculados.values())
        destinado_a_investimento = total_receita - total_gasto

        # Ajuste a contagem de Investimento/Dívida para se adequar à regra específica
        if "INVESTIMENTO_DIVIDA" in regras_alvo:
            # Se a regra usar um grupo combinado, calculamos o total de ambas as fontes
            investimento_e_divida = (
                destinado_a_investimento + grupos_calculados["DIVIDAS_EDUCACAO"]
            )
            grupos_calculados["INVESTIMENTO_DIVIDA"] = investimento_e_divida
            # Remove os grupos individuais para evitar duplicidade na resposta
            grupos_calculados.pop("DIVIDAS_EDUCACAO", None)
            grupos_calculados.pop("INVESTIMENTO_POUPANCA", None)

        # Formatar o resultado com % de Adesão
        resumo_adesao = {}
        for grupo, alvo_pct in regras_alvo.items():
            valor_real = grupos_calculados.get(grupo, 0.0)
            pct_real = (valor_real / total_receita) * 100
            resumo_adesao[grupo] = {
                "Alvo_Pct": alvo_pct * 100,
                "Real_Pct": pct_real,
                "Valor_Real": valor_real,
                "Alvo_Valor": total_receita * alvo_pct,
                "Status": "Acima"
                if pct_real > (alvo_pct * 100)
                else (
                    "Abaixo" if pct_real < (alvo_pct * 100) * 0.9 else "Atingido"
                ),  # Lógica simplificada
            }

        # Garante que o investimento não seja negativo
        if (
            "INVESTIMENTO_POUPANCA" in resumo_adesao
            and resumo_adesao["INVESTIMENTO_POUPANCA"]["Valor_Real"] < 0
        ):
            resumo_adesao["INVESTIMENTO_POUPANCA"]["Valor_Real"] = 0

        # Retorna um JSON para o LLM interpretar
        return f"Análise da Regra '{rule_name}':\n{json.dumps(resumo_adesao, indent=2)}"
