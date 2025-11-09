# src/finance/tools/recommend_rule_tool.py
from collections.abc import Callable  # Importar Callable

import pandas as pd
from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.schemas import RecomendarRegraIdealInput


class RecomendarRegraIdealTool(BaseTool):  # type: ignore[misc]
    name: str = "recomendar_regra_ideal"
    description: str = "Recomenda a melhor Regra de Ouro Financeira (ex: 50/30/20) com base no perfil e momento de vida do usuário."
    args_schema: type[BaseModel] = RecomendarRegraIdealInput

    # --- DIP: Depende de Callables ---
    def __init__(self, view_data_func: Callable[..., pd.DataFrame]) -> None:
        super().__init__()
        self.visualizar_dados = view_data_func
        self.aba_perfil = "Perfil Financeiro"

    # --- FIM DA MUDANÇA ---

    def run(self) -> str:
        print(f"LOG: Ferramenta '{self.name}' chamada: Sugerindo Regra de Ouro.")

        # --- DIP: Chama a função injetada ---
        df_perfil = self.visualizar_dados(aba_nome=self.aba_perfil)

        if df_perfil.empty or "Campo" not in df_perfil.columns:
            return "AVISO: Não foi possível encontrar o perfil do usuário. Por favor, peça para ele preencher a 'Renda Mensal Média' e 'Principal Objetivo' na aba de Perfil ou pelo chat."

        try:
            # Converte a tabela em um dicionário (Campo -> Valor)
            valores_perfil = df_perfil.set_index("Campo")["Valor"].to_dict()
        except KeyError:
            return "Erro: A aba 'Perfil Financeiro' parece estar mal formatada."

        fase_vida = str(valores_perfil.get("Fase de Vida", "")).lower()
        maior_meta = str(valores_perfil.get("Principal Objetivo", "")).lower()

        if not fase_vida and not maior_meta:
            return "AVISO: Não foi possível encontrar a 'Fase de Vida' ou 'Principal Objetivo' no perfil. A recomendação será genérica."

        # --- O DECISION ENGINE (Lógica do Consultor) ---
        regra_sugerida = "50/30/20"  # Padrão
        justificativa = "É a regra mais equilibrada, focada em manter uma divisão saudável entre gastos essenciais (50%), desejos (30%) e o futuro (20% para investimentos/dívida)."

        if "dívida" in fase_vida or "quitar" in maior_meta or "endividado" in fase_vida:
            regra_sugerida = "20/10/60/10"  # (Invest/Desejos/Essencial/Dívida)
            justificativa = (
                "Com base em sua meta de quitar dívidas, a regra 20/10/60/10 pode ser mais adequada. "
                "Ela foca 60% no essencial, 10% para lazer, 10% para pagamento acelerado de dívidas e 20% para investimentos futuros. "
                "Isso garante que você ataque o endividamento de forma segura."
            )
        elif "riqueza" in maior_meta or "crescendo" in fase_vida:
            regra_sugerida = "50/30/20"
            justificativa = (
                "Seu foco é a construção de riqueza. Manter a regra 50/30/20 com um foco rigoroso nos 20% de Investimento "
                "é uma excelente estratégia para acelerar a acumulação de patrimônio."
            )

        return f"RECOMENDAÇÃO: A regra ideal para a sua fase de vida é '{regra_sugerida}'. Justificativa: {justificativa}"
