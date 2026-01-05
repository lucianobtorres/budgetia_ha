from core.subscription.providers import SubscriptionProvider, SubscriptionStatus, Plan

class EntitlementService:
    """
    Serviço que verifica se o usuário tem acesso a funcionalidades específicas (Gatekeeper).
    """

    def __init__(self, provider: SubscriptionProvider):
        self.provider = provider

    def get_user_status(self, user_id: str) -> dict:
        return self.provider.get_subscription_status(user_id)

    def can_access_premium_features(self, user_id: str) -> bool:
        """Verifica se o usuário pode acessar recursos Premium (IA avançada, Sync, etc)."""
        status = self.provider.get_subscription_status(user_id)
        
        if status["status"] in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]:
            return True
        
        return False
