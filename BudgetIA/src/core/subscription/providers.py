from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import yaml
import os
import stripe

from core.logger import get_logger
from config import DATA_DIR, STRIPE_SECRET_KEY, DEPLOY_MODE

logger = get_logger("SubscriptionProvider")

class SubscriptionStatus:
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    FREE = "free" # Default fallback

class Plan:
    FREE = "free"
    PRO = "pro"

class SubscriptionProvider(ABC):
    @abstractmethod
    def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Retorna o status da assinatura do usuário."""
        pass

    @abstractmethod
    def create_checkout_session(self, user_id: str, plan: str) -> str:
        """Cria uma sessão de checkout e retorna a URL."""
        pass

    @abstractmethod
    def create_portal_session(self, user_id: str) -> str:
        """Cria uma sessão do portal de cliente e retorna a URL."""
        pass

class MockSubscriptionProvider(SubscriptionProvider):
    """Provedor simulado para desenvolvimento e self-hosted."""
    
    def __init__(self):
        self.users_file = os.path.join(DATA_DIR, "users.yaml")

    def _load_user_data(self, user_id: str) -> Dict[str, Any]:
        if not os.path.exists(self.users_file):
            return {}
        try:
            with open(self.users_file, "r") as f:
                data = yaml.safe_load(f) or {}
                # A estrutura é credentials -> usernames -> user_id
                return data.get("credentials", {}).get("usernames", {}).get(user_id, {})
        except Exception as e:
            logger.error(f"Erro ao ler users.yaml: {e}")
            return {}

    def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        user_data = self._load_user_data(user_id)
        
        # Lógica de Trial Mockado
        trial_end = user_data.get("trial_ends_at")
        role = user_data.get("role", "user")
        
        if role == "admin":
             return {
                "status": SubscriptionStatus.ACTIVE,
                "plan": Plan.PRO,
                "trial_end": None,
                "is_trial": False
            }

        is_trial = False
        status = SubscriptionStatus.FREE # Default é FREE se acabou o trial

        if trial_end:
            try:
                dt_end = datetime.fromisoformat(trial_end)
                if dt_end > datetime.now():
                    is_trial = True
                    status = SubscriptionStatus.TRIALING
            except ValueError:
                pass
        
        # Em modo SELF_HOSTED, todos são PRO se não tiver trial ou algo assim
        if DEPLOY_MODE == "SELF_HOSTED":
             return {
                "status": SubscriptionStatus.ACTIVE,
                "plan": Plan.PRO,
                "trial_end": None,
                "is_trial": False
            }

        return {
            "status": status,
            "plan": Plan.PRO if is_trial else Plan.FREE,
            "trial_end": trial_end if is_trial else None,
            "is_trial": is_trial
        }

    def create_checkout_session(self, user_id: str, plan: str) -> str:
        return "http://localhost:5173/profile?success=true&mock=true"

    def create_portal_session(self, user_id: str) -> str:
        return "http://localhost:5173/profile?portal=true&mock=true"


class StripeSubscriptionProvider(SubscriptionProvider):
    """Provedor real usando Stripe API."""
    
    def __init__(self):
        if not STRIPE_SECRET_KEY:
             logger.warning("STRIPE_SECRET_KEY não configurada. StripeProvider pode falhar.")
        stripe.api_key = STRIPE_SECRET_KEY

    def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        # TODO: Implementar busca real no Stripe usando customer_id salvo no users.yaml
        # Por enquanto, fallback para Mock logic ou FREE
        return MockSubscriptionProvider().get_subscription_status(user_id)

    def create_checkout_session(self, user_id: str, plan: str) -> str:
        # TODO: Implementar chamada real
        return "https://checkout.stripe.com/mock-session"

    def create_portal_session(self, user_id: str) -> str:
         # TODO: Implementar chamada real
        return "https://billing.stripe.com/mock-portal"
