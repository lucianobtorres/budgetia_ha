import requests
from typing import Any, Optional
from core.exceptions import (
    APIConnectionError,
    APIResponseError,
    AuthenticationError,
    NotFoundError,
    ServerError,
)

class BudgetAPIClient:
    """
    Cliente para comunicação com a API do BudgetIA.
    Permite que o Frontend (Streamlit) seja agnóstico à implementação do backend.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000", user_id: str = "default_user"):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-User-ID": user_id}

    def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        """Centralized request handler with exception mapping."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            
            # Raise HTTPError for bad responses (4xx, 5xx)
            response.raise_for_status()
            
            # Simple content handing
            if response.status_code == 204: # No Content
                return None
            try:
                return response.json()
            except ValueError:
                return response.content

        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Falha na conexão com servidor: {e}")
        except requests.exceptions.Timeout as e:
            raise APIConnectionError(f"Timeout na conexão com servidor: {e}")
        except requests.HTTPError as e:
             status_code = e.response.status_code
             if status_code in [401, 403]:
                 raise AuthenticationError(status_code, e.response.text)
             elif status_code == 404:
                 raise NotFoundError(status_code, f"Recurso não encontrado: {endpoint}")
             elif status_code >= 500:
                 raise ServerError(status_code, f"Erro interno do servidor: {e.response.text}")
             else:
                 raise APIResponseError(status_code, e.response.text)
        except Exception as e:
             raise APIConnectionError(f"Erro inesperado no cliente: {e}")

    def is_healthy(self) -> bool:
        """Verifica se a API está online."""
        try:
            self._make_request("GET", "/health", timeout=2)
            return True
        except Exception:
            return False

    def get_transactions(self, limit: int = 50) -> list[dict[str, Any]]:
        """Busca lista de transações."""
        return self._make_request("GET", "/transactions", params={"limit": limit}) # type: ignore

    def update_transactions_bulk(self, transactions: list[dict[str, Any]]) -> bool:
        """Atualiza a lista de transações em lote."""
        self._make_request("PUT", "/transactions/bulk", json=transactions)
        return True

    def send_chat_message(self, message: str, session_id: str = "default") -> str:
        """Envia mensagem para o Chat da API."""
        payload = {"message": message, "session_id": session_id}
        data = self._make_request("POST", "/chat/message", json=payload)
        # Ensure we return a string
        return str(data.get("response", "Erro: Resposta vazia da API."))

    def clear_chat_history(self) -> bool:
        """Limpa histórico de chat na API."""
        self._make_request("DELETE", "/chat/history")
        return True

    # --- Métodos de Dashboard ---

    def get_summary(self) -> dict[str, float]:
        """Busca resumo financeiro (receitas, despesas, saldo)."""
        return self._make_request("GET", "/dashboard/summary") # type: ignore

    def get_expenses_chart_data(self, top_n: int = 5) -> dict[str, float]:
        """Busca dados para o gráfico de despesas."""
        return self._make_request("GET", "/dashboard/expenses_by_category", params={"top_n": top_n}) # type: ignore

    def get_budgets_status(self) -> list[dict[str, Any]]:
        """Busca status dos orçamentos (apenas leitura/ativos)."""
        return self._make_request("GET", "/dashboard/budgets") # type: ignore

    def get_all_budgets(self) -> list[dict[str, Any]]:
        """Busca TODOS os orçamentos para edição."""
        return self._make_request("GET", "/budgets") # type: ignore

    def update_budgets_bulk(self, budgets: list[dict[str, Any]]) -> bool:
        """Atualiza a lista de orçamentos em lote."""
        self._make_request("PUT", "/budgets/bulk", json=budgets)
        return True

    def get_profile(self) -> list[dict[str, Any]]:
        """Busca dados do perfil."""
        return self._make_request("GET", "/profile") # type: ignore

    def update_profile(self, items: list[dict[str, Any]]) -> bool:
        """Atualiza dados do perfil."""
        self._make_request("PUT", "/profile/bulk", json=items)
        return True

    # --- Métodos de Memória (Brain) ---

    def get_memory_facts(self) -> list[dict[str, Any]]:
        """Busca fatos aprendidos pela IA."""
        return self._make_request("GET", "/profile/memory") # type: ignore

    def delete_memory_fact(self, fact_content: str) -> bool:
        """Esquece um fato específico."""
        # Codifica content na URL se necessário (requests faz isso se passar no path corretamente?)
        # Melhor enviar como query param? Não, a rota espera path param.
        # FastAPI lida com URL encoding, mas requests tem que mandar raw?
        # Simples concatenação funciona se requests.request lidar com encoding do path
        # Mas para segurança vamos usar requests.utils.quote se fosse complexo.
        # Aqui, assumimos que o fact_content é seguro o suficiente.
        # Se contiver barras, pode quebrar. O ideal seria passá-lo codificado?
        import urllib.parse
        encoded_content = urllib.parse.quote(fact_content)
        self._make_request("DELETE", f"/profile/memory/{encoded_content}")
        return True

    # --- Métodos de Regras (Watchdog) ---

    def get_watchdog_rules(self) -> list[dict[str, Any]]:
        """Busca regras ativas de monitoramento."""
        return self._make_request("GET", "/profile/rules") # type: ignore

    def delete_watchdog_rule(self, rule_id: str) -> bool:
        """Remove uma regra de monitoramento."""
        self._make_request("DELETE", f"/profile/rules/{rule_id}")
        return True

    def export_excel_bytes(self) -> tuple[bytes | None, str]:
        """
        Baixa o arquivo Excel da API.
        Retorna (bytes, filename).
        """
        url = f"{self.base_url}/dashboard/export"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            filename = "budget_export.xlsx"
            cd = response.headers.get("Content-Disposition")
            if cd and "filename=" in cd:
                filename = cd.split("filename=")[1].strip('"')
            return response.content, filename
        except Exception:
             # For export specifically, we might want to return None to signal UI
             # Or we raise exception if we want strict handling.
             # Keeping legacy behavior for now to avoid breaking Streamlit download button
             return None, "error.xlsx"

    def trigger_proactive_job(self) -> dict[str, Any]:
        """Dispara os jobs proativos para o usuário configurado."""
        try:
             return self._make_request("POST", "/jobs/run") # type: ignore
        except APIResponseError as e:
             return {"status": "error", "detail": str(e)}

    # --- Métodos de Notificação (Notification Center) ---

    def get_notifications(self, unread_only: bool = True) -> list[dict[str, Any]]:
        """Busca notificações."""
        try:
            return self._make_request("GET", "/notifications", params={"unread_only": unread_only}) # type: ignore
        except Exception:
            return [] # Fail safe for notifications

    def get_unread_count(self) -> int:
        """Retorna contagem de não lidas."""
        notifs = self.get_notifications(unread_only=True)
        return len(notifs)

    def mark_notification_read(self, notification_id: str) -> bool:
        """Marca notificação como lida."""
        self._make_request("POST", f"/notifications/{notification_id}/read")
        return True

    def delete_notification(self, notification_id: str) -> bool:
        """Exclui notificação."""
        self._make_request("DELETE", f"/notifications/{notification_id}")
        return True

    def mark_all_notifications_read(self) -> bool:
        """Marca todas como lidas."""
        self._make_request("POST", "/notifications/read-all")
        return True

    # --- Presence & Toasts ---
    
    def send_heartbeat(self) -> bool:
        """Envia sinal de vida para a API."""
        try:
            requests.post(f"{self.base_url}/presence/heartbeat", headers=self.headers, timeout=1)
            return True
        except Exception:
            return False

    def get_toasts(self) -> list[dict[str, Any]]:
        """Busca mensagens efêmeras (Toasts)."""
        try:
            # Short timeout, silent fail
            return self._make_request("GET", "/presence/toasts", timeout=1) # type: ignore
        except Exception:
            return []

    # --- Métodos de Onboarding (API-Driven) ---

    def get_onboarding_state(self) -> dict[str, Any]:
        """Retorna o estado atual do onboarding."""
        return self._make_request("GET", "/onboarding/state") # type: ignore

    def send_onboarding_message(self, text: str, extra_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Envia mensagem para o chat de onboarding."""
        payload = {"text": text, "context": extra_context}
        return self._make_request("POST", "/onboarding/chat", json=payload) # type: ignore

    def upload_onboarding_file(self, file_obj: Any, filename: str) -> dict[str, Any]:
        """Envia arquivo para o onboarding."""
        # Rebobina se for bytesIO
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        
        files = {"file": (filename, file_obj, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        return self._make_request("POST", "/onboarding/upload", files=files) # type: ignore

    def get_google_auth_url(self, redirect_uri: str) -> str | None:
        """Obtém URL de autenticação do Google."""
        try:
            resp = self._make_request("GET", "/onboarding/google-auth-url", params={"redirect_uri": redirect_uri})
            return resp.get("url") # type: ignore
        except Exception:
            return None

    def send_google_auth_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Envia código de auth do Google."""
        # Add timeout slightly larger for auth processing
        payload = {"code": code, "redirect_uri": redirect_uri}
        return self._make_request("POST", "/onboarding/google-auth", json=payload, timeout=10) # type: ignore

    def reset_account(self, fast_track: bool = False) -> bool:
        """Reseta a conta do usuário (Zona de Perigo)."""
        payload = {"fast_track": fast_track}
        self._make_request("POST", "/profile/reset", json=payload)
        return True
