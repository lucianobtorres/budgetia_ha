import sys
import os

# Adiciona src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from infrastructure.caching.redis_cache_service import RedisCacheService

def clear_cache():
    print("--- Clearing Cache for User ---")
    redis = RedisCacheService()
    if redis.enabled:
        # Padrão de chave definido na Factory: dfs:{username}
        keys = ["dfs:lucianobtorres"] # Hardcoded for the known user
        for k in keys:
            redis.invalidate(k)
        print("Done.")
    else:
        print("Redis disabled.")

if __name__ == "__main__":
    clear_cache()
