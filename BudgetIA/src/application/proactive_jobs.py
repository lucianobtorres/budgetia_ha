# src/app/proactive_jobs.py
import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finance.planilha_manager import PlanilhaManager

from application.notifications.channels.email_channel import EmailChannel
from application.notifications.channels.sms_channel import SMSChannel
from application.notifications.channels.telegram_channel import TelegramChannel
from application.notifications.channels.whatsapp_channel import WhatsAppChannel
from application.notifications.orchestrator import ProactiveNotificationOrchestrator
from application.notifications.rule_repository import RuleRepository
from application.notifications.rules.audit.subscription_auditor_rule import (
    SubscriptionAuditorRule,
)
from application.notifications.rules.economy.anomaly_detection_rule import (
    AnomalyDetectionRule,
)
from application.notifications.rules.economy.budget_overrun_rule import (
    BudgetOverrunRule,
)
from application.notifications.rules.economy.burn_rate_rule import BurnRateRule
from application.notifications.rules.economy.semantic_anomaly_rule import (
    SemanticAnomalyRule,
)
from core.llm_manager import LLMOrchestrator
from core.logger import get_logger
from core.user_config_service import UserConfigService

logger = get_logger("ProactiveJobs")


from application.notifications.rules.economy.recurring_expense_monitor import (  # noqa: E402
    RecurringExpenseMonitor,
)
from application.services.push_notification_service import (  # noqa: E402
    PushNotificationService,  # noqa: E402
)


# Helper para API de Inteligência listar o que temos
def get_default_rules(user_config_service: UserConfigService = None):
    """
    Retorna as regras padrão do sistema.
    Algumas regras podem precisar de config para inicialização (ex: ler keywords).
    """
    # Ler keywords do config se disponível para o SubscriptionAuditor
    sub_keywords = None
    if user_config_service:
        try:
            config = user_config_service.load_config()
            sub_keywords = config.get("comunicacao", {}).get("subscription_keywords")
        except Exception:
            pass

    return [
        BudgetOverrunRule(threshold_percent=0.9),
        BurnRateRule(days_threshold=5),
        AnomalyDetectionRule(std_dev_threshold=3.0, lookback_days=2),
        SubscriptionAuditorRule(days_lookback=30, custom_keywords=sub_keywords),
        RecurringExpenseMonitor(days_lookback=30, threshold_percent=1.2),
        SemanticAnomalyRule(threshold_similarity=0.35, lookback_n=15),  # Nova Regra
    ]


async def run_proactive_notifications(
    config_service: UserConfigService,
    llm_orchestrator: LLMOrchestrator,
    plan_manager: "PlanilhaManager",  # Dependencia Injetada
) -> dict[str, Any]:
    """
    Executa o sistema de notificações proativas para um usuário.
    Agora espera o PlanilhaManager já inicializado (via API).
    """
    logger.info(f"JOB PROATIVO: Iniciando para '{config_service.username}'")

    try:
        # Verifica caminho apenas para logging/debug, mas o manager já deve ter resolvido
        if not plan_manager:
            logger.error("JOB: PlanilhaManager nulo recebido.")
            return {
                "notifications_sent": 0,
                "rules_checked": 0,
                "failures": ["Manager is None"],
                "rules_triggered": 0,
            }

        planilha_path = config_service.get_planilha_path()
        logger.debug(
            f"JOB: Usando PlanilhaManager injetado (Arquivo: {planilha_path})..."
        )

        # 3. Registrar regras de negócio
        # Regras "Hardcoded" do sistema
        rules = get_default_rules()

        # Regras Dinâmicas (Jarvis Guard)
        repo = RuleRepository(config_service.get_user_dir())
        dynamic_rules = repo.get_all_rules()
        if dynamic_rules:
            logger.info(
                f"JOB: Carregando {len(dynamic_rules)} regras dinâmicas do repositório."
            )
            rules.extend(dynamic_rules)

        # 4. Registrar canais de notificação (Omnichannel)
        channels = [
            TelegramChannel(),
            WhatsAppChannel(),
            EmailChannel(),
            SMSChannel(),
        ]

        # 5. Instanciar Push Service
        push_service = PushNotificationService(config_service.config_dir)

        # 6. Criar e executar orchestrator
        orchestrator = ProactiveNotificationOrchestrator(
            rules=rules,
            channels=channels,
            config_service=config_service,
            push_service=push_service,  # Injeta o serviço de Push
        )

        result = await orchestrator.run(plan_manager)

        logger.info(f"JOB FINALIZADO para '{config_service.username}'")
        logger.info(f"Notificações enviadas: {result['notifications_sent']}")
        logger.debug(f"Regras verificadas: {result['rules_checked']}")
        if result["failures"]:
            logger.warning(f"Falhas: {len(result['failures'])}")

        return result

    except Exception as e:
        logger.error(f"JOB: Falha ao executar notificações proativas: {e}")
        return {
            "notifications_sent": 0,
            "failures": [str(e)],
            "rules_checked": 0,
            "rules_triggered": 0,
        }


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
    logger.warning(
        "check_missing_daily_transport() é uma função legada. "
        "Use run_proactive_notifications() diretamente."
    )

    # Chama a nova implementação
    asyncio.run(run_proactive_notifications(config_service, llm_orchestrator))  # type: ignore[call-arg]


async def run_data_sanitizer_job(
    config_service: UserConfigService,
    llm_orchestrator: LLMOrchestrator,
    plan_manager: "PlanilhaManager",
) -> dict[str, Any]:
    """
    Executa a 'Faxina' (Data Sanitization) via Caso de Uso.
    """
    logger.info(f"JOB SANITIZER: Iniciando para '{config_service.username}'")
    try:
        result = plan_manager.faxinar_transacoes()
        if result.get("processed", 0) > 0:
            plan_manager.salvar()
        return result
    except Exception as e:
        logger.error(f"JOB SANITIZER: Erro fatal: {e}")
        return {"status": "error", "message": str(e)}


async def run_behavior_learning_job(
    config_service: UserConfigService,
    llm_orchestrator: LLMOrchestrator,
    pm: "PlanilhaManager",
) -> dict:
    """Stub for behavior learning if referenced elsewhere"""
    # TODO: Implement actual behavior learning
    return {"status": "skipped", "message": "Not implemented yet"}
