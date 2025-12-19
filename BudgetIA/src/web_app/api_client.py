import requests
from typing import Any, Optional

class BudgetAPIClient:
    """
    Cliente para comunicação com a API do BudgetIA.
    Permite que o Frontend (Streamlit) seja agnóstico à implementação do backend.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000", user_id: str = "default_user"):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-User-ID": user_id}
        # Em produção, adicionaríamos timeout e retry logic

    def is_healthy(self) -> bool:
        """Verifica se a API está online."""
        try:
            response = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_transactions(self, limit: int = 50) -> list[dict[str, Any]]:
        """Busca lista de transações."""
        try:
            response = requests.get(f"{self.base_url}/transactions", headers=self.headers, params={"limit": limit})
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Erro ao buscar transações: {e}")
            return []

    def update_transactions_bulk(self, transactions: list[dict[str, Any]]) -> bool:
        """Atualiza a lista de transações em lote."""
        try:
            response = requests.put(f"{self.base_url}/transactions/bulk", headers=self.headers, json=transactions)
            return response.status_code == 200
        except Exception:
            return False

    def send_chat_message(self, message: str, session_id: str = "default") -> str:
        """Envia mensagem para o Chat da API."""
        try:
            payload = {"message": message, "session_id": session_id}
            response = requests.post(f"{self.base_url}/chat/message", headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "Erro: Resposta vazia da API.")
        except requests.HTTPError as e:
            return f"Erro na API ({e.response.status_code}): {e.response.text}"
        except Exception as e:
            return f"Erro de conexão: {e}"

    def clear_chat_history(self) -> bool:
        """Limpa histórico de chat na API."""
        try:
            response = requests.delete(f"{self.base_url}/chat/history", headers=self.headers)
            return response.status_code == 200
        except Exception:
            return False

    # --- Métodos de Dashboard ---

    def get_summary(self) -> dict[str, float]:
        """Busca resumo financeiro (receitas, despesas, saldo)."""
        try:
            response = requests.get(f"{self.base_url}/dashboard/summary", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}

    def get_expenses_chart_data(self, top_n: int = 5) -> dict[str, float]:
        """Busca dados para o gráfico de despesas."""
        try:
            response = requests.get(f"{self.base_url}/dashboard/expenses_by_category", headers=self.headers, params={"top_n": top_n})
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}

    def get_budgets_status(self) -> list[dict[str, Any]]:
        """Busca status dos orçamentos (apenas leitura/ativos)."""
        try:
            response = requests.get(f"{self.base_url}/dashboard/budgets", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []

    def get_all_budgets(self) -> list[dict[str, Any]]:
        """Busca TODOS os orçamentos para edição."""
        try:
            response = requests.get(f"{self.base_url}/budgets", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []

    def update_budgets_bulk(self, budgets: list[dict[str, Any]]) -> bool:
        """Atualiza a lista de orçamentos em lote."""
        try:
            response = requests.put(f"{self.base_url}/budgets/bulk", headers=self.headers, json=budgets)
            return response.status_code == 200
        except Exception:
            return False

    def get_profile(self) -> list[dict[str, Any]]:
        """Busca dados do perfil."""
        try:
            response = requests.get(f"{self.base_url}/profile", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []

    def update_profile(self, items: list[dict[str, Any]]) -> bool:
        """Atualiza dados do perfil."""
        try:
            response = requests.put(f"{self.base_url}/profile/bulk", headers=self.headers, json=items)
            return response.status_code == 200
        except Exception:
            return False

    def export_excel_bytes(self) -> tuple[bytes | None, str]:
        """
        Baixa o arquivo Excel da API.
        Retorna (bytes, filename).
        """
        try:
            response = requests.get(f"{self.base_url}/dashboard/export", headers=self.headers)
            if response.status_code == 200:
                filename = "budget_export.xlsx"
                # Tenta pegar nome do header
                cd = response.headers.get("Content-Disposition")
                if cd and "filename=" in cd:
                    filename = cd.split("filename=")[1].strip('"')
                return response.content, filename
            return None, "error.xlsx"
        except Exception:
            return None, "error.xlsx"

    def trigger_proactive_job(self) -> dict[str, Any]:
        """Dispara os jobs proativos para o usuário configurado."""
        try:
            response = requests.post(f"{self.base_url}/jobs/run", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            print(f"Erro ao rodar job ({response.status_code}): {response.text}")
            return {"status": "error", "detail": response.text}
        except Exception as e:
             print(f"Erro de conexão no job: {e}")
             return {"status": "error", "detail": str(e)}

    # --- Métodos de Notificação (Notification Center) ---

    def get_notifications(self, unread_only: bool = True) -> list[dict[str, Any]]:
        """Busca notificações."""
        try:
            params = {"unread_only": unread_only}
            response = requests.get(f"{self.base_url}/notifications", headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []

    def get_unread_count(self) -> int:
        """Retorna contagem de não lidas."""
        notifs = self.get_notifications(unread_only=True)
        return len(notifs)

    def mark_notification_read(self, notification_id: str) -> bool:
        """Marca notificação como lida."""
        try:
            response = requests.post(f"{self.base_url}/notifications/{notification_id}/read", headers=self.headers)
            return response.status_code == 200
        except Exception:
            return False

    def delete_notification(self, notification_id: str) -> bool:
        """Exclui notificação."""
        try:
            response = requests.delete(f"{self.base_url}/notifications/{notification_id}", headers=self.headers)
            return response.status_code == 200
        except Exception:
            return False

    def mark_all_notifications_read(self) -> bool:
        """Marca todas como lidas."""
        try:
            response = requests.post(f"{self.base_url}/notifications/read-all", headers=self.headers)
            return response.status_code == 200
        except Exception:
            return False

    # --- Presence & Toasts ---
    
    def send_heartbeat(self) -> bool:
        """Envia sinal de vida para a API."""
        try:
            # Timeout curto para não travar UI
            requests.post(f"{self.base_url}/presence/heartbeat", headers=self.headers, timeout=1)
            return True
        except Exception:
            return False

    def get_toasts(self) -> list[dict[str, Any]]:
        """Busca mensagens efêmeras (Toasts)."""
        try:
            response = requests.get(f"{self.base_url}/presence/toasts", headers=self.headers, timeout=1)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []
