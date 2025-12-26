from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class PushSubscription:
    endpoint: str
    keys_auth: str
    keys_p256dh: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    device_name: Optional[str] = None
