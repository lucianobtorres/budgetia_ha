# src/bot.py
import logging
import os
import sys
from pathlib import Path

# --- 1. Adicionar 'src' ao sys.path (como fizemos no start.py) ---
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# --- 2. Imports do nosso Backend ---
# --- 3. Imports do Telegram ---
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config

# --- CORREÇÃO: Importar do seu arquivo correto ---
from app.chat_history_manager import JsonHistoryManager
from app.chat_service import ChatService
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider
from initialization.system_initializer import initialize_financial_system
from web_app.utils import load_persistent_config

# Configura o logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 4. Carregar o "Cérebro" (Backend) UMA VEZ ---
print("--- INICIALIZANDO BOT DO TELEGRAM ---")

# Carrega o token (que você colocou no .env)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN não encontrado no arquivo .env!")

# Carrega o LLM Orchestrator (global)
primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
llm_orchestrator = LLMOrchestrator(primary_provider=primary_provider)
llm_orchestrator.get_configured_llm()

# Carrega a configuração do usuário (para saber qual planilha usar)
user_config = load_persistent_config()
planilha_path = user_config.get("planilha_path")
if not planilha_path:
    raise ValueError("Nenhum 'planilha_path' encontrado no user_config.json!")

print(f"BOT: Carregando sistema para a planilha: {planilha_path}")
plan_manager, agent_runner, _, _ = initialize_financial_system(
    planilha_path, llm_orchestrator
)
if not agent_runner or not plan_manager:
    raise RuntimeError("Falha ao inicializar o sistema financeiro para o bot.")

# --- A CORREÇÃO ESTÁ AQUI ---
# Precisamos converter config.DATA_DIR (que é str) para um Path()
bot_history_path = Path(config.DATA_DIR) / "telegram_chat_history.json"
# --- FIM DA CORREÇÃO ---

bot_history_manager = JsonHistoryManager(str(bot_history_path))
print(f"BOT: Usando arquivo de histórico: {bot_history_path}")

# Cria o ChatService GLOBAL para o bot
bot_chat_service = ChatService(agent_runner, bot_history_manager)

print("--- BOT PRONTO E OUVINDO ---")

# --- 5. Handlers do Telegram ---


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para o comando /start"""
    bot_history_manager.clear()  # Limpa o histórico
    await update.message.reply_text(
        "Olá! Sou seu assistente financeiro. Meu cérebro foi reiniciado e "
        "meu histórico de chat com você foi limpo. Como posso ajudar?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para qualquer mensagem de texto."""
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.message.chat_id
    print(f"BOT: Recebida mensagem de {chat_id}: '{user_text}'")

    # Mostra "Digitando..." no Telegram
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # --- A MÁGICA ACONTECE AQUI ---
        response = bot_chat_service.handle_message(user_text)
        # --- FIM DA MÁGICA ---

        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
        await update.message.reply_text(
            f"Desculpe, ocorreu um erro interno ao processar sua solicitação: {e}"
        )


def main() -> None:
    """Função principal para rodar o bot."""
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
