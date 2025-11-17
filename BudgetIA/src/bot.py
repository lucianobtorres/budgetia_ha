# src/bot.py
import logging
import os
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
from app.chat_history_manager import JsonHistoryManager
from app.chat_service import ChatService
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider
from core.user_config_service import UserConfigService
from initialization.system_initializer import initialize_financial_system

# 1. Encontra o diretório 'src' onde este arquivo está.
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Encontra a raiz do projeto (um nível acima do 'src').
PROJECT_ROOT = os.path.dirname(SRC_DIR)

# 3. Adiciona a RAIZ do projeto ao sys.path.
# Isso permite imports como 'from src.core import ...'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 4. Adiciona o PRÓPRIO 'src' ao sys.path.
# Isso permite imports como 'from core import ...' (embora o 'from src.core' seja mais explícito)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

print(f"--- DEBUG: SYS.PATH ATUALIZADO (para {__file__}) ---")
print(f"ROOT: {PROJECT_ROOT}")
print(f"SRC: {SRC_DIR}")
print("--- INICIANDO IMPORTS DA APLICAÇÃO ---")

# Configura o logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_USERNAME = "jsmith"

# --- 4. Carregar o "Cérebro" (Backend) UMA VEZ ---
print("--- INICIALIZANDO BOT DO TELEGRAM ---")

# Carrega o token (que você colocou no .env)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    TELEGRAM_TOKEN = ""
    raise ValueError("TELEGRAM_TOKEN não encontrado no arquivo .env!")


def load_global_services() -> tuple[ChatService | None, UserConfigService | None]:
    try:
        # Carrega o LLM Orchestrator (global)
        primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
        llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
        llm_orchestrator.get_configured_llm()

        print(f"BOT: Carregando sistema para o usuário '{BOT_USERNAME}'...")

        # Instancia o serviço para o usuário específico
        config_service = UserConfigService(BOT_USERNAME)
        planilha_path = config_service.get_planilha_path()
        if not planilha_path:
            raise ValueError(
                f"Planilha não configurada para o usuário '{BOT_USERNAME}' no UserConfigService."
            )

        print(f"BOT: Carregando sistema para a planilha: {planilha_path}")
        plan_manager, agent_runner, _, _ = initialize_financial_system(
            planilha_path, llm_orchestrator, config_service=config_service
        )
        if not agent_runner or not plan_manager:
            raise RuntimeError("Falha ao inicializar o sistema financeiro para o bot.")

        # --- A CORREÇÃO ESTÁ AQUI ---
        # Precisamos converter config.DATA_DIR (que é str) para um Path()
        bot_history_path = config_service.config_dir / "telegram_chat_history.json"
        # --- FIM DA CORREÇÃO ---

        bot_history_manager = JsonHistoryManager(str(bot_history_path))
        print(f"BOT: Usando arquivo de histórico: {bot_history_path}")

        # Cria o ChatService GLOBAL para o bot
        bot_chat_service = ChatService(agent_runner, bot_history_manager)

        print("--- BOT PRONTO E OUVINDO ---")
        return bot_chat_service, config_service

    except Exception as e:
        logger.critical(f"ERRO FATAL AO INICIAR O BOT: {e}", exc_info=True)
        return None, None


bot_chat_service, config_service = load_global_services()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para o comando /start"""
    if bot_chat_service:
        bot_chat_service.history_manager.clear()  # Limpa o histórico
    await update.message.reply_text(
        "Olá! Sou seu assistente financeiro. Meu cérebro foi reiniciado e "
        "meu histórico de chat com você foi limpo. Como posso ajudar?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para qualquer mensagem de texto."""
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    if config_service:
        # Salva o chat_id no user_config.json para o scheduler usar
        config_service.save_comunicacao_field("telegram_chat_id", chat_id)

    user_text = update.message.text
    print(f"BOT: Recebida mensagem de {chat_id}: '{user_text}'")

    # Mostra "Digitando..." no Telegram
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        if not bot_chat_service:
            raise Exception("ChatService não foi inicializado.")

        # --- A MÁGICA ACONTECE AQUI ---
        user_id_key = f"{BOT_USERNAME}:{chat_id}"
        response = bot_chat_service.handle_message(user_text, user_id_key)
        # --- FIM DA MÁGICA ---

        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
        await update.message.reply_text(
            f"Desculpe, ocorreu um erro interno ao processar sua solicitação: {e}"
        )


def main() -> None:
    """Função principal para rodar o bot."""
    if not bot_chat_service or not config_service:
        logger.critical("Serviços globais não puderam ser carregados. Encerrando bot.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adiciona os handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Inicia o bot (ele fica rodando 24/7)
    application.run_polling()


if __name__ == "__main__":
    main()
