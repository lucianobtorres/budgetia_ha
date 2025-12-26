
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


from application.services.push_notification_service import PushNotificationService

class ProactiveNotificationOrchestrator:
    """
    Coordena a verificação de regras e o envio de notificações de forma proativa.
    Agora suporta Múltiplos Canais (Omnichannel) e Push Notifications.
    """

    def __init__(
        self,
        rules: list[IFinancialRule],
        channels: list[INotificationChannel],
        config_service: UserConfigService,
        push_service: PushNotificationService | None = None, # NEW Dependency
    ):
        """
        Inicializa o orchestrator.
        """
        self.rules = rules
        # Mapeia nome -> instância
        self.channels_map = {ch.channel_name: ch for ch in channels}
        # Garante que InAppChannel esteja disponível
        if "in_app" not in self.channels_map:
            self.channels_map["in_app"] = InAppChannel()
            
        self.config_service = config_service
        self.notification_service = NotificationService(config_service, push_service) # Pass Push Service
        self.presence_service = PresenceService()

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
            # Verifica se o canal existe (foi injetado) e se está configurado pelo usuário
            if channel and channel.is_configured_for_user(user_config):
                recipient = channel.get_recipient_id(user_config)
                if recipient:
                    targets.append((channel, recipient))
                    print(f"LOG (Orchestrator): Canal '{ch_name}' selecionado para '{recipient}'.")

        return targets

    async def run(self, plan_manager: PlanilhaManager) -> dict[str, Any]:
        stats: dict[str, Any] = {
            "notifications_sent": 0,
            "rules_checked": 0,
            "rules_triggered": 0,
            "failures": [],
        }

        try:
            # 1. Carregar dados
            transactions_df = plan_manager.visualizar_dados("Visão Geral e Transações")
            budgets_df = plan_manager.visualizar_dados("Meus Orçamentos")
            user_profile: dict[str, Any] = {} # Todo: carregar profile

        except Exception as e:
            print(f"ERRO (Orchestrator): Falha ao carregar dados: {e}")
            stats["failures"].append(f"data_load_error: {e}")
            return stats

        # 2. Config & Seleção de Canais
        user_config = self.config_service.load_config()
        targets = self._select_channels(user_config)
        
        if not targets:
            print("AVISO (Orchestrator): Nenhum canal (nem In-App?) disponível.")
        
        # 3. Executar Regras
        for rule in self.rules:
            stats["rules_checked"] += 1
            print(f"\nLOG (Orchestrator): Executando regra '{rule.rule_name}'...")

            try:
                result = rule.should_notify(transactions_df, budgets_df, user_profile)

                if result.triggered:
                    stats["rules_triggered"] += 1
                    message = result.to_message()
                    
                    # Salva no Notification Center (DB Local)
                    self.notification_service.add_notification(
                        message=message.text, 
                        category=message.category,
                        priority=message.priority.value if hasattr(message.priority, 'value') else "medium"
                    )

                    # BROADCAST para todos os canais alvo
                    for channel, recipient in targets:
                        try:
                            # Envio Async
                            # Nota: 'send' deve retornar True/False
                            success = await channel.send(recipient, message)
                            if success:
                                stats["notifications_sent"] += 1
                                print(f"LOG (Orchestrator): Enviado para {recipient} via {channel.channel_name}.")
                            else:
                                stats["failures"].append(f"{rule.rule_name}:{channel.channel_name}:failed")
                        except Exception as ex:
                            stats["failures"].append(f"{rule.rule_name}:{channel.channel_name}:error")
                            print(f"ERRO Envio {channel.channel_name}: {ex}")

                else:
                    print(f"LOG (Orchestrator): Regra '{rule.rule_name}' ok (não acionada).")

            except Exception as e:
                print(f"ERRO (Orchestrator): Falha na regra '{rule.rule_name}': {e}")
                stats["failures"].append(f"{rule.rule_name}: {e}")

        return stats
