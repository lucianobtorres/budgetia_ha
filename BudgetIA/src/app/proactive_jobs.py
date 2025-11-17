# src/app/proactive_jobs.py

import asyncio

# --- 1. NOVOS IMPORTS ---
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# --- FIM NOVOS IMPORTS ---
import config
from app.notification_sender import TelegramSender  # O "Carteiro"
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider
from core.user_config_service import UserConfigService
from initialization.system_initializer import initialize_financial_system


def check_missing_daily_transport(
    config_service: UserConfigService, llm_orchestrator: LLMOrchestrator
) -> None:
    """
    Verifica se o usuário lançou despesa de 'Transporte' nas últimas 48h
    e envia uma notificação proativa via Telegram.
    """
    print(f"\n--- JOB PROATIVO: {datetime.now()} ---")
    print("Executando 'check_missing_daily_transport'...")

    try:
        # 1. Carregar configuração
        user_config = config_service.load_config()
        planilha_path = config_service.get_planilha_path()
        # --- 2. CARREGAR CONFIGS DE COMUNICAÇÃO ---
        comms_config = user_config.get("comunicacao", {})
        telegram_chat_id = comms_config.get("telegram_chat_id")

        telegram_token = os.getenv("TELEGRAM_TOKEN")

        if not telegram_token:
            print("ERRO JOB: TELEGRAM_TOKEN não encontrado no .env. Pulando.")
            return

        if not telegram_chat_id:
            print(
                "ERRO JOB: 'telegram_chat_id' não encontrado no user_config.json. Pulando."
            )
            return

        if not planilha_path or not Path(planilha_path).exists():
            print(
                f"ERRO JOB: Planilha não encontrada para {config_service.username}. Pulando."
            )
            return
        # --- FIM CARREGAR CONFIGS ---

        # 2. Inicializar o "Cérebro" (Backend)
        primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
        llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
        llm_orchestrator.get_configured_llm()

        plan_manager, _, _, _ = initialize_financial_system(
            planilha_path, llm_orchestrator, config_service=config_service
        )

        if not plan_manager:
            print(
                f"ERRO JOB: Falha ao inicializar PlanilhaManager para {planilha_path}"
            )
            return

        # 3. Executar a Regra de Negócio (Lendo o Excel)
        print(f"JOB: Verificando transações em {planilha_path}...")
        df_transacoes = plan_manager.visualizar_dados(config.NomesAbas.TRANSACOES)

        if df_transacoes.empty:
            print("JOB: Nenhuma transação encontrada.")
            return

        df_transacoes[config.ColunasTransacoes.DATA] = pd.to_datetime(
            df_transacoes[config.ColunasTransacoes.DATA]
        )
        two_days_ago = datetime.now() - timedelta(days=2)

        transport_recent = df_transacoes[
            (df_transacoes[config.ColunasTransacoes.CATEGORIA] == "Transporte")
            & (df_transacoes[config.ColunasTransacoes.DATA] >= two_days_ago)
        ]

        # 4. Agir (Substituindo o 'print' pela chamada real)
        if transport_recent.empty:
            print("JOB: Nenhuma despesa de 'Transporte' encontrada nos últimos 2 dias.")

            # --- 4. CHAMADA REAL PARA O TELEGRAM ---
            message = (
                "Olá! Notei que você não registra gastos com 'Transporte' há 2 dias. "
                "Gostaria de adicionar um gasto agora?\n\n"
                "(Eu sou seu assistente proativo. Esta é uma mensagem automática.)"
            )

            try:
                sender = TelegramSender(token=telegram_token)
                # Usamos asyncio.run() para chamar a função async de dentro
                # desta função síncrona (do schedule)
                asyncio.run(sender.send_message(telegram_chat_id, message))

            except Exception as e:
                print(f"ERRO JOB: Falha ao tentar enviar mensagem via Telegram: {e}")
            # --- FIM DA CHAMADA REAL ---

        else:
            print("JOB: Despesa de 'Transporte' encontrada. Nenhuma ação necessária.")

    except Exception as e:
        print(f"ERRO JOB: Falha ao executar 'check_missing_daily_transport': {e}")
