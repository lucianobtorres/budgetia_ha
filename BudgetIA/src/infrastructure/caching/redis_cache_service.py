import os
import redis
import pickle
import pandas as pd
from typing import Any, Optional
from config import UPSTASH_REDIS_URL
from core.logger import get_logger

logger = get_logger("RedisCache")

class RedisCacheService:
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        
        if UPSTASH_REDIS_URL:
            try:
                # Fix protocol for Upstash if needed
                url = UPSTASH_REDIS_URL
                if url.startswith("redis://") and not url.startswith("rediss://"):
                    url = url.replace("redis://", "rediss://")
                
                # ssl_cert_reqs=None needed for some environments to avoid SSL errors
                self.redis_client = redis.from_url(url, ssl_cert_reqs=None)
                self.redis_client.ping() # Test connection
                self.enabled = True
                logger.info("Redis Cache Service Connected Successfully. 🚀")
            except Exception as e:
                logger.warning(f"Falha ao conectar Redis Cache: {e}")
                self.enabled = False

    def get_entry(self, key: str) -> tuple[Any, Optional[str]]:
        """Recupera (Dados, Timestamp) do cache."""
        if not self.enabled:
            return None, None
        
        try:
            data = self.redis_client.get(key)
            if data:
                # Expects a tuple (data_object, timestamp_str)
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"ERRO Cache Read ({key}): {e}")
        return None, None

    def set_entry(self, key: str, data: Any, timestamp: str, ttl_seconds: int = 3600) -> bool:
        """Salva (Dados, Timestamp) no cache."""
        if not self.enabled:
            return False
            
        try:
            payload = (data, timestamp)
            serialized_data = pickle.dumps(payload)
            self.redis_client.setex(key, ttl_seconds, serialized_data)
            return True
        except Exception as e:
            logger.error(f"ERRO Cache Write ({key}): {e}")
            return False

    def invalidate(self, key: str) -> bool:
        """Remove uma chave do cache."""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"ERRO Cache Invalidate ({key}): {e}")
            return False
