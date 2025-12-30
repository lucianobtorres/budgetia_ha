
# src/app/notifications/orchestrator.py
from typing import Any

import config
from application.notifications.channels.base_channel import INotificationChannel
from application.notifications.channels.in_app_channel import InAppChannel
from application.notifications.rules.base_rule import IFinancialRule
from application.services.notification_service import NotificationService
from application.services.presence_service import PresenceService
from core.user_config_service import UserConfigService
from finance.planilha_manager import PlanilhaManager


from core.behavior.user_behavior_service import UserBehaviorService
from application.services.push_notification_service import PushNotificationService
from core.logger import get_logger

logger = get_logger("NotificationOrchestrator")

class ProactiveNotificationOrchestrator:
    """
    Coordena a verificação de regras e o envio de notificações de forma proativa.
    Agora suporta Múltiplos Canais (Omnichannel) e Push Notifications.
    Também integra com a 'Memória Adaptativa' (UserBehaviorService).
    """

    def __init__(
        self,
        rules: list[IFinancialRule],
        channels: list[INotificationChannel],
        config_service: UserConfigService,
        push_service: PushNotificationService | None = None,
    ):
        """
        Inicializa o orchestrator.
        """
        self.rules = rules
        self.channels_map = {ch.channel_name: ch for ch in channels}
        if "in_app" not in self.channels_map:
            self.channels_map["in_app"] = InAppChannel()
            
        self.config_service = config_service
        self.notification_service = NotificationService(config_service, push_service)
        self.presence_service = PresenceService()
        self.behavior_service = UserBehaviorService(config_service.username) # Instancia a memória

    def _select_channels(
        self, user_config: dict[str, Any]
    ) -> list[tuple[INotificationChannel, str]]:
        """
        Seleciona TODOS os canais configurados e válidos para envio (Omnichannel Broadcast).
        Retorna lista de (Channel, RecipientID).
        """
        targets = []
        username = self.config_service.username

        # 1. In-App (Sempre ativo)
        in_app = self.channels_map.get("in_app")
        if in_app:
            targets.append((in_app, username))

        # 2. Canais Externos
        external_channels = ["whatsapp", "telegram", "sms", "email"]
        
        for ch_name in external_channels:
            channel = self.channels_map.get(ch_name)
            if channel and channel.is_configured_for_user(user_config):
                recipient = channel.get_recipient_id(user_config)
                if recipient:
                    targets.append((channel, recipient))
                    logger.debug(f"Canal '{ch_name}' selecionado para '{recipient}'.")

        return targets

    async def run(self, plan_manager: PlanilhaManager) -> dict[str, Any]:
        stats: dict[str, Any] = {
            "notifications_sent": 0,
            "rules_checked": 0,
            "rules_triggered": 0,
            "failures": [],
            "rules_silenced": 0 
        }

        try:
            # 1. Carregar dados
            transactions_df = plan_manager.visualizar_dados("Visão Geral e Transações")
            budgets_df = plan_manager.visualizar_dados("Meus Orçamentos")
            user_profile: dict[str, Any] = {} # Todo: carregar profile

        except Exception as e:
            logger.error(f"Falha ao carregar dados: {e}")
            stats["failures"].append(f"data_load_error: {e}")
            return stats

        # 2. Config & Seleção de Canais
        user_config = self.config_service.load_config()
        targets = self._select_channels(user_config)
        
        if not targets:
            logger.warning("Nenhum canal (nem In-App?) disponível.")
        
        # 3. Executar Regras
        for rule in self.rules:
            stats["rules_checked"] += 1

            # --- JARVIS CHECK: A regra deve ser silenciada? ---
            if self.behavior_service.should_silence_rule(rule.rule_name, threshold=3):
                logger.info(f"Regra '{rule.rule_name}' SILENCIADA pelo Jarvis (ignorada frequentemente).")
                stats["rules_silenced"] += 1
                continue # Pula esta regra

            logger.info(f"Executando regra '{rule.rule_name}'...")

            try:
                result = rule.should_notify(transactions_df, budgets_df, user_profile)

                if result.triggered:
                    stats["rules_triggered"] += 1
                    message = result.to_message()
                    
                    # Salva no Notification Center (DB Local)
                    notification_id = self.notification_service.add_notification(
                        message=message.text, 
                        category=message.category,
                        priority=message.priority.value if hasattr(message.priority, 'value') else "medium"
                    )

                    # --- JARVIS LOG: Registra que a regra foi disparada (aguardando feedback) ---
                    # O ID da notificação pode ser usado no futuro para linkar o feedback
                    
                    # BROADCAST para todos os canais alvo
                    for channel, recipient in targets:
                        try:
                            success = await channel.send(recipient, message)
                            if success:
                                stats["notifications_sent"] += 1
                                logger.info(f"Enviado para {recipient} via {channel.channel_name}.")
                            else:
                                stats["failures"].append(f"{rule.rule_name}:{channel.channel_name}:failed")
                        except Exception as ex:
                            stats["failures"].append(f"{rule.rule_name}:{channel.channel_name}:error")
                            logger.error(f"Erro Envio {channel.channel_name}: {ex}")

                else:
                    logger.debug(f"Regra '{rule.rule_name}' ok (não acionada).")

            except Exception as e:
                logger.error(f"Falha na regra '{rule.rule_name}': {e}")
                stats["failures"].append(f"{rule.rule_name}: {e}")

        return stats
