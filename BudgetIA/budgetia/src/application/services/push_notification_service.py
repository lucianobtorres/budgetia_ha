import json
import os
import logging
from pathlib import Path
from typing import Any
from pywebpush import webpush, WebPushException

from application.notifications.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

class PushNotificationService:
    """
    Service to manage Push Subscriptions and dispatch messages via WebPush.
    Stores subscriptions in 'data/push_subscriptions.json'.
    """

    def __init__(self, data_dir: Path):
        self.file_path = data_dir / "push_subscriptions.json"
        
        # Load VAPID details from Environment
        self.private_key = os.getenv("VAPID_PRIVATE_KEY")
        self.claim_email = os.getenv("VAPID_CLAIM_EMAIL")
        
        # Check if Private Key is a path or string
        self.private_key_path = None
        if self.private_key and os.path.exists(self.private_key):
            self.private_key_path = self.private_key
            self.private_key = None # Clear string if it's a path

    def _load_subscriptions(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save_subscriptions(self, subs: list[dict[str, Any]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(subs, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(f"Failed to save push subscriptions: {e}")

    def subscribe(self, subscription: PushSubscription) -> None:
        """Saves a new subscription."""
        subs = self._load_subscriptions()
        
        # Check if already exists (by endpoint)
        existing = next((s for s in subs if s["endpoint"] == subscription.endpoint), None)
        if existing:
            # Update keys if changed
            existing["keys_auth"] = subscription.keys_auth
            existing["keys_p256dh"] = subscription.keys_p256dh
            existing["user_id"] = subscription.user_id # Update ownership
            existing["updated_at"] = str(subscription.created_at)
        else:
            new_sub = {
                "endpoint": subscription.endpoint,
                "keys_auth": subscription.keys_auth,
                "keys_p256dh": subscription.keys_p256dh,
                "user_id": subscription.user_id,
                "created_at": str(subscription.created_at),
                "device_name": subscription.device_name
            }
            subs.append(new_sub)
        
        self._save_subscriptions(subs)
        logger.info(f"New Push Subscription saved for user {subscription.user_id}")

    def unsubscribe(self, endpoint: str) -> bool:
        """Removes a subscription."""
        subs = self._load_subscriptions()
        initial_len = len(subs)
        subs = [s for s in subs if s["endpoint"] != endpoint]
        
        if len(subs) < initial_len:
            self._save_subscriptions(subs)
            return True
        return False

    def send_notification(self, user_id: str, message: str, title: str = "BudgetIA", tag: str = "notification") -> int:
        """
        Sends a push notification to all devices of a user.
        Returns number of successful sends.
        """
        if not (self.private_key or self.private_key_path) or not self.claim_email:
            logger.warning("VAPID keys not configured. Skipping Push Notification.")
            return 0

        subs = self._load_subscriptions()
        user_subs = [s for s in subs if s.get("user_id") == user_id or s.get("user_id") == "bundleia_user_id"] # Fallback hardcoded ID from app
        
        # If no user_id specific subs found, maybe broadcast? No, strict.
        # However, for single user app using 'bundleia_user_id' as default:
        if not user_subs and not user_id:
             user_subs = subs # Broadcast to all if user_id is None (admin alert)

        payload = json.dumps({
            "title": title,
            "body": message,
            "icon": "/pwa-192x192.png",
            "badge": "/pwa-192x192.png",
            "tag": tag,
            "url": "/" 
        })

        sent_count = 0
        for sub in user_subs:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub["endpoint"],
                        "keys": {
                            "p256dh": sub["keys_p256dh"],
                            "auth": sub["keys_auth"]
                        }
                    },
                    data=payload,
                    vapid_private_key=self.private_key or self.private_key_path,
                    vapid_claims={"sub": self.claim_email},
                    ttl=12 * 60 * 60 # 12 hours
                )
                sent_count += 1
            except WebPushException as ex:
                logger.error(f"WebPush failed: {ex}")
                if ex.response and ex.response.status_code == 410:
                    # Expired/Gone
                    self.unsubscribe(sub["endpoint"])
            except Exception as e:
                logger.error(f"Push dispatch error: {e}")

        return sent_count
