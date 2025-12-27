import redis
import hashlib
from contextlib import contextmanager
from config import UPSTASH_REDIS_URL

class RedisLockManager:
    """
    Gerencia locks distribuídos usando Redis para garantir exclusividade 
    no acesso aos arquivos Excel em ambientes multi-processo.
    """
    _client = None

    @classmethod
    def get_client(cls):
         if cls._client is None:
             if UPSTASH_REDIS_URL and (
                 UPSTASH_REDIS_URL.startswith("redis://") or 
                 UPSTASH_REDIS_URL.startswith("rediss://") or 
                 UPSTASH_REDIS_URL.startswith("unix://")
             ):
                 # Ensure protocol compatibility if necessary
                 url = UPSTASH_REDIS_URL
                 if url.startswith("redis://") and "upstash" in url:
                      url = url.replace("redis://", "rediss://")
                 
                 try:
                    cls._client = redis.from_url(url, decode_responses=False)
                 except Exception as e:
                    print(f"AVISO: Falha ao conectar Redis Cache: {e}")
                    cls._client = None
             else:
                 print("AVISO: UPSTASH_REDIS_URL inválida ou não configurada. Locks distribuídos DESATIVADOS.")
         return cls._client

    def __init__(self, resource_id: str):
        """
        Args:
            resource_id: Identificador único do recurso (ex: caminho do arquivo)
        """
        self.client = self.get_client()
        # Create a safe key from resource_id
        safe_id = hashlib.md5(resource_id.encode()).hexdigest()
        self.lock_name = f"lock:resource:{safe_id}"

    @contextmanager
    def acquire(self, timeout_seconds: int = 30, blocking_timeout: int = 10):
        """
        Context manager para adquirir o lock.
        Args:
            timeout_seconds: Tempo máximo que o lock permanece ativo (auto-release).
            blocking_timeout: Tempo máximo esperando para adquirir o lock.
        """
        if not self.client:
            # Fallback para no-op se Redis não estiver disponível
            # TODO: Idealmente fallback para FileLock local se single-server
            yield None
            return

        lock = self.client.lock(
            self.lock_name, 
            timeout=timeout_seconds,
            blocking_timeout=blocking_timeout
        )
        
        acquired = lock.acquire()
        if not acquired:
            raise TimeoutError(f"Não foi possível adquirir o lock para {self.lock_name} após {blocking_timeout}s")
        
        try:
            yield lock
        finally:
            if lock.owned():
                lock.release()
