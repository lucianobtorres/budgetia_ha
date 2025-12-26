
from typing import Type, Optional, Any
from pydantic import BaseModel, Field

from core.base_tool import BaseTool
from application.notifications.rule_repository import RuleRepository
from application.notifications.rules.dynamic_rule import DynamicThresholdRule
from core.user_config_service import UserConfigService


class CreateAlertSchema(BaseModel):
    category: str = Field(
        ..., description="Categoria de gasto a ser monitorada (ex: 'Alimentação', 'Uber')."
    )
    threshold: float = Field(
        ..., description="Valor limite que, se excedido, dispara o alerta."
    )
    period: str = Field(
        "monthly",
        description="Período de monitoramento: 'monthly' (Mensal - Padrão) ou 'weekly' (Semanal).",
    )
    message: Optional[str] = Field(
        None,
        description="Mensagem personalizada para o alerta. Se não informado, usa padrão.",
    )


class CreateAlertTool(BaseTool): # type: ignore[misc]
    """
    Ferramenta que permite ao agente criar alertas de monitoramento de gastos
    solicitados pelo usuário.
    Ex: 'Me avise se eu gastar mais de 500 em Jogos'.
    """

    name = "create_spending_alert"
    description = (
        "Cria um monitoramento automático (alerta) para gastos excessivos em uma categoria. "
        "Use quando o usuário pedir para ser avisado sobre gastos acima de um valor."
    )
    args_schema: Type[BaseModel] = CreateAlertSchema

    def __init__(self, config_service: UserConfigService):
        self.config_service = config_service
        self.repo = RuleRepository(config_service.get_user_dir())

    def run(
        self,
        category: str,
        threshold: float,
        period: str = "monthly",
        message: Optional[str] = None,
    ) -> str:
        try:
            # Normalizar input
            period = period.lower()
            if period not in ["monthly", "weekly"]:
                period = "monthly"

            # 1. Verificar se já existe regra para essa categoria (qualquer período) e remover
            # Isso evita duplicidade lógica (ex: ter regra semanal E mensal para Cafés)
            existing_rules = self.repo.get_all_rules()
            for r in existing_rules:
                if getattr(r, "category", "").lower() == category.lower():
                    # Se for DynamicThresholdRule, removemos para substituir pela nova
                    if isinstance(r, DynamicThresholdRule):
                        self.repo.remove_rule(r.id)

            # Criar ID único baseado na categoria e período
            rule_id = f"{category.lower().replace(' ', '_')}_{period}"

            rule = DynamicThresholdRule(
                rule_id=rule_id,
                category=category,
                threshold=threshold,
                period=period,
                custom_message=message,
            )

            self.repo.add_rule(rule)

            return (
                f"✅ Alerta Criado com Sucesso!\n"
                f"Vou monitorar os gastos com '{category}'.\n"
                f"Se passar de R$ {threshold:.2f} ({'Mensal' if period == 'monthly' else 'Semanal'}), "
                "eu te aviso."
            )

        except Exception as e:
            return f"❌ Erro ao criar alerta: {str(e)}"
