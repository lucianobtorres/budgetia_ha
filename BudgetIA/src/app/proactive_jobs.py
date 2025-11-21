# src/app/proactive_jobs.py
import asyncio

from app.notifications.channels.telegram_channel import TelegramChannel
from app.notifications.orchestrator import ProactiveNotificationOrchestrator
from app.notifications.rules.transport_missing_rule import TransportMissingRule
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from initialization.system_initializer import initialize_financial_system


async def run_proactive_notifications(
    config_service: UserConfigService,
    llm_orchestrator: LLMOrchestrator,
) -> dict[str, int]:
    """
    Executa o sistema de notificações proativas para um usuário.

    Coordena a inicialização do sistema financeiro, registro de regras e canais,
    e execução do orchestrator.

    Args:
        config_service: Serviço de configuração do usuário.
        llm_orchestrator: Orquestrador de LLM (para futuras regras IA-powered).

    Returns:
        Estatísticas de execução do orchestrator.
    """
    print(f"\n--- JOB PROATIVO: Iniciando para '{config_service.username}' ---")

    try:
        # 1. Obter caminho da planilha
        planilha_path = config_service.get_planilha_path()
        if not planilha_path:
            print(
                f"ERRO JOB: Planilha não encontrada para {config_service.username}. Pulando."
            )
            return {"notifications_sent": 0}

        # 2. Inicializar sistema financeiro
        print(f"JOB: Inicializando sistema financeiro para {planilha_path}...")
        plan_manager, _, _, _ = initialize_financial_system(
            planilha_path, llm_orchestrator, config_service=config_service
        )

        if not plan_manager:
            print(
                f"ERRO JOB: Falha ao inicializar PlanilhaManager para {planilha_path}"
            )
            return {"notifications_sent": 0}

        # 3. Registrar regras de negócio
        # Futuro: carregar de configuração ou plugin system
        rules = [
            TransportMissingRule(days_threshold=2),
            # BudgetOverageRule(),  # Futuro
            # UnusualSpendingRule(),  # Futuro
        ]

        # 4. Registrar canais de notificação
        # Futuro: detectar canais disponíveis automaticamente
        channels = [
            TelegramChannel(),  # Busca token do .env automaticamente
            # WhatsAppChannel(),  # Futuro
            # InAppChannel(),  # Futuro
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
        return {"notifications_sent": 0, "failures": [str(e)]}


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
