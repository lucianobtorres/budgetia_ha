from pydantic import BaseModel

from core.base_tool import BaseTool
from finance.planilha_manager import PlanilhaManager
from finance.schemas import RecomendarRegraIdealInput


class RecomendarRegraIdealTool(BaseTool):
    name: str = "recomendar_regra_ideal"
    description: str = (
        "Recomenda a melhor Regra de Ouro Financeira (ex: 50/30/20) com base no perfil e momento de vida do usuário. "
        "Usa a 'Fase de Vida' e a 'Maior Meta' registradas para dar um conselho personalizado."
    )
    args_schema: type[BaseModel] = RecomendarRegraIdealInput

    def __init__(self, planilha_manager: PlanilhaManager):
        super().__init__()
        self.planilha_manager = planilha_manager
        self.aba_perfil = "Metas Financeiras"

    def run(self) -> str:
        print(f"LOG: Ferramenta '{self.name}' chamada: Sugerindo Regra de Ouro.")

        df_metas = self.planilha_manager.visualizar_dados(aba_nome=self.aba_perfil)

        # Tenta encontrar o perfil do usuário (o último registro que começa com 'Perfil:')
        perfil = (
            df_metas[
                df_metas["Nome da Meta"].astype(str).str.contains("Perfil:", na=False)
            ]
            .iloc[::-1]
            .head(1)
        )

        if perfil.empty:
            return "AVISO: Não foi possível encontrar o perfil de vida do usuário. Por favor, use a ferramenta 'coletar_perfil_usuario' primeiro."

        # Extrai os dados do perfil
        obs = perfil.iloc[0]["Observações"]
        fase_vida = ""
        maior_meta = ""

        if ";" in obs:
            fase_vida = obs.split("Fase: ")[1].split(";")[0].strip().lower()
            maior_meta = obs.split("Meta Principal: ")[1].split(";")[0].strip().lower()

        # --- O DECISION ENGINE (Lógica do Consultor) ---
        regra_sugerida = "50/30/20"  # Padrão
        justificativa = "É a regra mais equilibrada, focada em manter uma divisão saudável entre gastos essenciais, desejos e o futuro (investimento/dívida)."

        if "dívidas pesadas" in fase_vida or "quitar" in maior_meta:
            regra_sugerida = "20/10/60/10"  # Prioriza Essenciais (60%) e Dívida (10%)
            justificativa = "Com base em sua meta de quitar dívidas e sua fase de 'Pagamento de Dívidas Pesadas', a regra 20/10/60/10 é a mais adequada. Ela garante que 60% da sua renda cubra o essencial e destina 10% do seu foco para a quitação acelerada de dívidas, permitindo que você ataque o endividamento de forma segura."

        elif "riqueza" in maior_meta or "renda crescendo" in fase_vida:
            regra_sugerida = "50/30/20"
            justificativa = "Seu foco é a construção de riqueza. Manter a regra 50/30/20 com um foco rigoroso nos 20% de Investimento é a melhor estratégia para acelerar a acumulação de patrimônio."

        # 4. Retornar a Sugestão para o LLM
        return f"RECOMENDAÇÃO: A regra ideal para a sua fase de vida é '{regra_sugerida}'. Justificativa: {justificativa}"
