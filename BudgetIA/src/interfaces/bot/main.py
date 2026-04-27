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

from core.logger import get_logger
from core.user_config_service import UserConfigService
from interfaces.web_app.api_client import BudgetAPIClient

# Configura o logging
logger = get_logger("Bot")

# 1. Encontra o diretório onde este arquivo está (src/bot)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 2. Encontra o diretório 'src' (um nível acima)
SRC_DIR = os.path.dirname(CURRENT_DIR)
# 3. Encontra a raiz do projeto (um nível acima do 'src')
PROJECT_ROOT = os.path.dirname(SRC_DIR)

# 3. Adiciona a RAIZ do projeto ao sys.path.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

BOT_USERNAME = "jsmith"

logger.info("INICIALIZANDO BOT DO TELEGRAM (MODO API CLI)")

# Carrega o token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN não encontrado no arquivo .env!")

# URL da API (pode vir de env)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


def wait_for_api(url: str, timeout: int = 60) -> bool:
    """Aguarda a API ficar disponível."""
    import time

    import requests

    start_time = time.time()
    logger.info(f"Aguardando API em {url} ficar pronta...")
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/api/health")
            if response.status_code == 200:
                logger.info("✅ API detectada e pronta!")
                return True
        except:  # noqa: E722
            pass
        time.sleep(2)
    logger.error("❌ Timeout aguardando API.")
    return False


def load_api_client() -> tuple[BudgetAPIClient | None, UserConfigService | None]:
    try:
        logger.info(f"Conectando à API em {API_URL} como '{BOT_USERNAME}'...")

        # Instancia o cliente da API
        # O Client já cuida dos headers de autenticação simples (X-User-ID)
        client = BudgetAPIClient(base_url=API_URL, user_id=BOT_USERNAME)

        # Teste de conexão (Health Check)
        if not client.is_healthy():
            logger.warning(
                "AVISO: Não foi possível conectar à API durante a inicialização."
            )
        else:
            logger.info("Conexão com a API estabelecida com sucesso.")

        # Carrega config service APENAS para salvar o chat_id localmente (Scheduler)
        config_service = UserConfigService(BOT_USERNAME)

        return client, config_service

    except Exception as e:
        logger.critical(f"ERRO AO INICIAR CLIENTE DO BOT: {e}", exc_info=True)
        return None, None


api_client, config_service = load_api_client()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para o comando /start"""
    if api_client:
        api_client.clear_chat_history()
    await update.message.reply_text(
        "Olá! Sou seu assistente financeiro (via API). Estou pronto! 🤖💸"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para qualquer mensagem de texto."""
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id

    # Salva o ID para o Scheduler (localmente, pois o scheduler roda local)
    if config_service:
        config_service.save_comunicacao_field("telegram_chat_id", chat_id)

    user_text = update.message.text
    logger.info(f"Mensagem Recebida ({chat_id}): '{user_text}'")

    # Mostra "Digitando..." no Telegram
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        if not api_client:
            raise Exception("Cliente da API não está disponível.")

        # --- ENVIA PARA A API ---
        # session_id pode ser o chat_id para manter conversas separadas se a API suportar
        response = api_client.send_chat_message(user_text, session_id=str(chat_id))
        # ------------------------

        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
        await update.message.reply_text(
            f"Desculpe, ocorreu um erro interno ao processar sua solicitação: {e}"
        )


def main() -> None:
    """Função principal para rodar o bot."""
    # Aguarda API antes de tentar carregar o cliente
    if not wait_for_api(API_URL):
        logger.warning(
            "Prosseguindo sem confirmação da API (tentativas de conexão podem falhar)."
        )

    global api_client, config_service
    api_client, config_service = load_api_client()

    if not api_client or not config_service:
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
