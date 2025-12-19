# src/app/proactive_jobs.py
import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from finance.planilha_manager import PlanilhaManager

from app.notifications.channels.telegram_channel import TelegramChannel
from app.notifications.channels.whatsapp_channel import WhatsAppChannel
from app.notifications.channels.email_channel import EmailChannel
from app.notifications.channels.sms_channel import SMSChannel
from app.notifications.orchestrator import ProactiveNotificationOrchestrator
from app.notifications.rules.economy.transport_missing_rule import TransportMissingRule
from app.notifications.rules.economy.budget_overrun_rule import BudgetOverrunRule
from app.notifications.rules.audit.subscription_auditor_rule import SubscriptionAuditorRule
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from app.notifications.rule_repository import RuleRepository


async def run_proactive_notifications(
    config_service: UserConfigService,
    llm_orchestrator: LLMOrchestrator,
    plan_manager: "PlanilhaManager" # Dependencia Injetada
) -> dict[str, int]:
    """
    Executa o sistema de notificações proativas para um usuário.
    Agora espera o PlanilhaManager já inicializado (via API).
    """
    print(f"\n--- JOB PROATIVO: Iniciando para '{config_service.username}' ---")

    try:
        # Verifica caminho apenas para logging/debug, mas o manager já deve ter resolvido
        if not plan_manager:
             print("ERRO JOB: PlanilhaManager nulo recebido.")
             return {"notifications_sent": 0, "rules_checked": 0, "failures": ["Manager is None"], "rules_triggered": 0}

        planilha_path = config_service.get_planilha_path()
        print(f"JOB: Usando PlanilhaManager injetado (Arquivo: {planilha_path})...")

        # 3. Registrar regras de negócio
        # Regras "Hardcoded" do sistema
        rules = [
            # Configurado para 2 dias de inatividade
            TransportMissingRule(days_threshold=2),
            BudgetOverrunRule(threshold_percent=0.9),
        ]
        
        # Regras Dinâmicas (Jarvis Guard)
        repo = RuleRepository(config_service.get_user_dir())
        dynamic_rules = repo.get_all_rules()
        if dynamic_rules:
            print(f"JOB: Carregando {len(dynamic_rules)} regras dinâmicas do repositório.")
            rules.extend(dynamic_rules)

        # 4. Registrar canais de notificação (Omnichannel)
        channels = [
            TelegramChannel(),
            WhatsAppChannel(),
            EmailChannel(),
            SMSChannel(),
        ]

        # 5. Criar e executar orchestrator
        orchestrator = ProactiveNotificationOrchestrator(
            rules=rules,
            channels=channels,
            config_service=config_service,
        )

        result = await orchestrator.run(plan_manager)

        print(f"\n--- JOB FINALIZADO para '{config_service.username}' ---")
        print(f"Notificações enviadas: {result['notifications_sent']}")
        print(f"Regras verificadas: {result['rules_checked']}")
        print(f"Falhas: {len(result['failures'])}")

        return result

    except Exception as e:
        print(f"ERRO JOB: Falha ao executar notificações proativas: {e}")
        return {"notifications_sent": 0, "failures": [str(e)], "rules_checked": 0, "rules_triggered": 0}


def check_missing_daily_transport(
    config_service: UserConfigService, llm_orchestrator: LLMOrchestrator
) -> None:
    """
    FUNÇÃO LEGADA para compatibilidade com scheduler.py.

    Esta função é um wrapper síncrono que chama o novo sistema assíncrono.
    Manter enquanto scheduler.py não for atualizado.

    Args:
        config_service: Serviço de configuração do usuário.
        llm_orchestrator: Orquestrador de LLM.
    """
    print(
        "AVISO: check_missing_daily_transport() é uma função legada. "
        "Use run_proactive_notifications() diretamente."
    )

    # Chama a nova implementação
    asyncio.run(run_proactive_notifications(config_service, llm_orchestrator))
