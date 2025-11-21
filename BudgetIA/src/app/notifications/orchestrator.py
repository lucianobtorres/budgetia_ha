# src/app/notifications/orchestrator.py
from typing import Any

import config
from app.notifications.channels.base_channel import INotificationChannel
from app.notifications.rules.base_rule import IFinancialRule
from core.user_config_service import UserConfigService
from finance.planilha_manager import PlanilhaManager


class ProactiveNotificationOrchestrator:
    """
    Orquestrador do sistema de notificações proativas.

    Responsabilidade:
    1. Executar todas as regras de negócio
    2. Selecionar canal apropriado para cada notificação
    3. Enviar notificações através dos canais
    4. Rastrear estatísticas de execução
    """

    def __init__(
        self,
        rules: list[IFinancialRule],
        channels: list[INotificationChannel],
        config_service: UserConfigService,
    ):
        """
        Inicializa o orchestrator.

        Args:
            rules: Lista de regras de negócio a executar.
            channels: Lista de canais disponíveis para envio.
            config_service: Serviço de configuração do usuário.
        """
        self.rules = rules
        self.channels = {ch.channel_name: ch for ch in channels}
        self.config_service = config_service

    def _select_channel(
        self, user_config: dict[str, Any]
    ) -> INotificationChannel | None:
        """
        Seleciona o melhor canal para o usuário.

        Lógica simples (v1):
        - Usa primeiro canal configurado
        - Futuro: respeitar preferências, fallback, etc.

        Args:
            user_config: Configuração do usuário.

        Returns:
            Canal selecionado ou None se nenhum disponível.
        """
        for channel in self.channels.values():
            if channel.is_configured_for_user(user_config):
                print(
                    f"LOG (Orchestrator): Canal '{channel.channel_name}' selecionado."
                )
                return channel

        print("LOG (Orchestrator): Nenhum canal configurado para este usuário.")
        return None

    async def run(self, plan_manager: PlanilhaManager) -> dict[str, Any]:
        """
        Executa todas as regras e envia notificações necessárias.

        Args:
            plan_manager: Gerenciador de dados financeiros.

        Returns:
            Estatísticas de execução:
            {
                "rules_checked": int,
                "rules_triggered": int,
                "notifications_sent": int,
                "failures": list[str]
            }
        """
        print("\n--- INICIANDO ORCHESTRATOR DE NOTIFICAÇÕES PROATIVAS ---")

        stats = {
            "rules_checked": 0,
            "rules_triggered": 0,
            "notifications_sent": 0,
            "failures": [],
        }

        # 1. Carregar dados do usuário
        try:
            transactions_df = plan_manager.visualizar_dados(config.NomesAbas.TRANSACOES)
            budgets_df = plan_manager.visualizar_dados(config.NomesAbas.ORCAMENTOS)
            profile_df = plan_manager.visualizar_dados(
                config.NomesAbas.PERFIL_FINANCEIRO
            )

            # Converter perfil para dict (simplificado)
            user_profile = {}
            if not profile_df.empty and "Campo" in profile_df.columns:
                user_profile = dict(zip(profile_df["Campo"], profile_df["Valor"]))

        except Exception as e:
            print(f"ERRO (Orchestrator): Falha ao carregar dados: {e}")
            stats["failures"].append(f"data_loading: {e}")
            return stats

        # 2. Obter configuração do usuário
        user_config = self.config_service.load_config()

        # 3. Selecionar canal
        selected_channel = self._select_channel(user_config)
        if not selected_channel:
            print("AVISO (Orchestrator): Nenhum canal disponível. Não há onde enviar.")
            stats["failures"].append("no_channel_configured")
            return stats

        recipient_id = selected_channel.get_recipient_id(user_config)
        if not recipient_id:
            print(
                "ERRO (Orchestrator): Canal selecionado mas recipient_id não encontrado."
            )
            stats["failures"].append("recipient_id_missing")
            return stats

        # 4. Executar todas as regras
        for rule in self.rules:
            stats["rules_checked"] += 1
            print(f"\nLOG (Orchestrator): Executando regra '{rule.rule_name}'...")

            try:
                result = rule.should_notify(transactions_df, budgets_df, user_profile)

                if result.triggered:
                    stats["rules_triggered"] += 1
                    print(f"LOG (Orchestrator): Regra '{rule.rule_name}' ACIONADA!")

                    # Converter para mensagem
                    message = result.to_message()

                    # Enviar via canal
                    success = await selected_channel.send(recipient_id, message)

                    if success:
                        stats["notifications_sent"] += 1
                        print(
                            f"LOG (Orchestrator): Notificação enviada com sucesso via {selected_channel.channel_name}."
                        )
                    else:
                        stats["failures"].append(f"{rule.rule_name}: send_failed")
                else:
                    print(f"LOG (Orchestrator): Regra '{rule.rule_name}' não acionada.")

            except Exception as e:
                print(
                    f"ERRO (Orchestrator): Falha ao executar regra '{rule.rule_name}': {e}"
                )
                stats["failures"].append(f"{rule.rule_name}: {e}")

        print("\n--- ORCHESTRATOR FINALIZADO ---")
        print(f"Estatísticas: {stats}")
        return stats
