# src/interfaces/web_app/api_client.py
import requests

from core.logger import get_logger

logger = get_logger("APIClient")


class BudgetAPIClient:
    def __init__(self, base_url: str, user_id: str):
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.headers = {"X-User-ID": user_id, "Content-Type": "application/json"}

    def is_healthy(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao verificar saúde da API: {e}")
            return False

    def send_chat_message(self, message: str, session_id: str = "default") -> str:
        try:
            payload = {"message": message, "session_id": session_id}
            response = requests.post(
                f"{self.base_url}/api/chat/message",
                json=payload,
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "Sem resposta da API.")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para API: {e}")
            return f"Erro na comunicação com a IA: {e}"

    def clear_chat_history(self) -> bool:
        try:
            response = requests.delete(
                f"{self.base_url}/api/chat/history", headers=self.headers, timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao limpar histórico na API: {e}")
            return False

    def get_chat_history(self) -> list:
        try:
            response = requests.get(
                f"{self.base_url}/api/chat/history", headers=self.headers, timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao recuperar histórico na API: {e}")
            return []
