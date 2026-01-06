# src/app/proactive_jobs.py
import asyncio

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finance.planilha_manager import PlanilhaManager

from application.notifications.channels.telegram_channel import TelegramChannel
from application.notifications.channels.whatsapp_channel import WhatsAppChannel
from application.notifications.channels.email_channel import EmailChannel
from application.notifications.channels.sms_channel import SMSChannel
from application.notifications.orchestrator import ProactiveNotificationOrchestrator
from application.notifications.rules.economy.transport_missing_rule import TransportMissingRule
from application.notifications.rules.economy.budget_overrun_rule import BudgetOverrunRule
from application.notifications.rules.audit.subscription_auditor_rule import SubscriptionAuditorRule
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from application.notifications.rule_repository import RuleRepository
from core.logger import get_logger

logger = get_logger("ProactiveJobs")


from application.services.push_notification_service import PushNotificationService

from application.notifications.rules.economy.recurring_expense_monitor import RecurringExpenseMonitor

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
        TransportMissingRule(days_threshold=2),
        BudgetOverrunRule(threshold_percent=0.9),
        SubscriptionAuditorRule(days_lookback=30, custom_keywords=sub_keywords),
        RecurringExpenseMonitor(days_lookback=30, threshold_percent=1.2)
    ]

async def run_proactive_notifications(
    config_service: UserConfigService,
    llm_orchestrator: LLMOrchestrator,
    plan_manager: "PlanilhaManager" # Dependencia Injetada
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
             return {"notifications_sent": 0, "rules_checked": 0, "failures": ["Manager is None"], "rules_triggered": 0}

        planilha_path = config_service.get_planilha_path()
        logger.debug(f"JOB: Usando PlanilhaManager injetado (Arquivo: {planilha_path})...")

        # 3. Registrar regras de negócio
        # Regras "Hardcoded" do sistema
        rules = get_default_rules()
        
        # Regras Dinâmicas (Jarvis Guard)
        repo = RuleRepository(config_service.get_user_dir())
        dynamic_rules = repo.get_all_rules()
        if dynamic_rules:
            logger.info(f"JOB: Carregando {len(dynamic_rules)} regras dinâmicas do repositório.")
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
            push_service=push_service, # Injeta o serviço de Push
        )

        result = await orchestrator.run(plan_manager)

        logger.info(f"JOB FINALIZADO para '{config_service.username}'")
        logger.info(f"Notificações enviadas: {result['notifications_sent']}")
        logger.debug(f"Regras verificadas: {result['rules_checked']}")
        if result['failures']:
            logger.warning(f"Falhas: {len(result['failures'])}")

        return result

    except Exception as e:
        logger.error(f"JOB: Falha ao executar notificações proativas: {e}")
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
    logger.warning(
        "check_missing_daily_transport() é uma função legada. "
        "Use run_proactive_notifications() diretamente."
    )

    # Chama a nova implementação
    asyncio.run(run_proactive_notifications(config_service, llm_orchestrator)) # type: ignore[call-arg]

async def run_data_sanitizer_job(
    config_service: UserConfigService,
    llm_orchestrator: LLMOrchestrator,
    plan_manager: "PlanilhaManager"
) -> dict[str, Any]:
    """
    Executa a 'Faxina' (Data Sanitization).
    Varre itens classificados como 'Outros' ou 'A Classificar' e tenta re-classificar com IA.
    """
    logger.info(f"JOB SANITIZER: Iniciando para '{config_service.username}'")
    
    # DEBUG LOGGING TO FILE
    import os
    try:
        with open("logs/__sanitizer.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- EXEC: {config_service.username} ---\n")
    except: pass
    
    def log_debug(msg):
        logger.info(msg)
        try:
            with open("logs/__sanitizer.log", "a", encoding="utf-8") as f:
                f.write(f"{msg}\n")
        except: pass

    try:
        from config import ColunasTransacoes
        
        # 1. Carregar Transações
        # (Cache ja deve estar ok via Manager)
        df = plan_manager.transaction_repo.get_all_transactions()
        
        log_debug(f"Total Transactions: {len(df)}")
        if not df.empty and ColunasTransacoes.CATEGORIA in df.columns:
            counts = df[ColunasTransacoes.CATEGORIA].value_counts()
            log_debug(f"Categories Distribution:\n{counts}")

        if df.empty or ColunasTransacoes.CATEGORIA not in df.columns:
            return {"status": "skipped", "reason": "No transactions or missing category column"}

        # 2. Filtrar Alvos (Outros, A Classificar ou VAZIOS)
        target_categories = ["Outros", "A Classificar"]
        
        def is_target(val):
            s = str(val).strip()
            # Alvo se for nulo, vazio, ou estiver na lista de alvos
            return (not s) or (s == "nan") or (s == "None") or (s in target_categories)

        mask = df[ColunasTransacoes.CATEGORIA].apply(is_target)
        target_indices = df.index[mask]
        
        log_debug(f"Targets Found indices: {len(target_indices)}")
        
        if len(target_indices) == 0:
            log_debug("JOB SANITIZER: Nenhuma transação pendente de classificação.")
            return {"status": "success", "processed": 0, "message": "Nenhuma transação para classificar."}
            
        # 3. Preparar Descrições Únicas
        descriptions = df.loc[target_indices, ColunasTransacoes.DESCRICAO].unique().tolist()
        descriptions = [str(d).strip() for d in descriptions if d and str(d).strip()]
        
        log_debug(f"Unique Descriptions to Classify: {descriptions}")
        
        if not descriptions:
            return {"status": "success", "processed": 0}

        # 4. Classificar em Lote (Reutilizando ImportService)
        # Precisamos instanciar ImportService. Ele precisa de CategoryRepo (via manager) e LLM.
        from finance.services.import_service import ImportService
        
        service = ImportService(llm_orchestrator, plan_manager.category_repo, plan_manager.transaction_repo)
        
        mapping = service.classify_batch(descriptions)
        log_debug(f"LLM Mapping Result: {mapping}")
        
        if not mapping:
            log_debug("JOB SANITIZER: IA não retornou mapeamentos.")
            return {"status": "warning", "processed": 0, "message": "IA não retornou sugestões."}
            
        # Normalizar mapping para busca insensitiva
        normalized_map = {k.strip().lower(): v for k, v in mapping.items()}
            
        # 5. Aplicar Atualizações no DataFrame
        changes_count = 0
        for idx in target_indices:
            original_desc = str(df.at[idx, ColunasTransacoes.DESCRICAO]).strip()
            
            # Tenta match exato primeiro
            new_cat = mapping.get(original_desc)
            
            # Tenta match insensitivo
            if not new_cat:
                 new_cat = normalized_map.get(original_desc.lower())
            
            log_debug(f"Reviewing '{original_desc}': New Cat '{new_cat}'")
            
            # Se achou e é diferente da atual E diferente de 'Outros'/'A Classificar' (se for a mesma coisa não muda nada, mas se mudou de Outros -> Transporte ok)
            if new_cat and new_cat not in target_categories:
                df.at[idx, ColunasTransacoes.CATEGORIA] = new_cat
                changes_count += 1
                log_debug(f" >>> APPLIED CHANGE: {original_desc} -> {new_cat}")
                
        # 6. Salvar
        if changes_count > 0:
            log_debug(f"Saving {changes_count} changes...")
            plan_manager.transaction_repo.save_transactions(df)
            log_debug(f"JOB SANITIZER: {changes_count} transações atualizadas com sucesso!")
            
            
            # Invalida cache de categorias se necessário (se criou novas)
            # Mas aqui salvamos direto no DF. O repo cuida de cache?
            # TransactionRepo usa DataContext que gerencia DF em memoria.
            # Se novas categorias surgiram, próxima leitura de categorias vai achar?
            # CategoryRepo lê de categorias.csv, mas ImportService NÃO adiciona ao categorias.csv automaticamente?
            # ImportService.classify_batch pode retornar categoria nova.
            # Precisamos adicionar novas categorias ao CategoryRepo se elas não existirem!
            
            return {"status": "success", "processed": changes_count, "details": f"{changes_count} itens classificados."}
        else:
            logger.info("JOB SANITIZER: Nenhuma mudança aplicável encontrada (IA retornou mesmas categorias ou falhou).")
            return {"status": "success", "processed": 0, "message": "IA não sugeriu mudanças válidas."}

    except Exception as e:
        logger.error(f"JOB SANITIZER: Erro fatal: {e}")
        return {"status": "error", "message": str(e)}

async def run_behavior_learning_job(
    config_service: UserConfigService,
    llm_orchestrator: LLMOrchestrator,
    pm: "PlanilhaManager"
) -> dict:
     """Stub for behavior learning if referenced elsewhere"""
     # TODO: Implement actual behavior learning
     return {"status": "skipped", "message": "Not implemented yet"}
