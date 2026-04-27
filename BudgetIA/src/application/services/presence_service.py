import json
from datetime import datetime
from typing import Any

import config
from core.cache_service import CacheService
from core.logger import get_logger

logger = get_logger("PresenceService")


class PresenceService:
    """
    Serviço de Presença e Tempo Real.
    - Híbrido: Usa Redis (Upstash) se disponível, senão usa memória (dict).
    """

    # Estado global compartilhado (para quando não houver Redis)
    _memory_last_seen: dict[str, datetime] = {}
    _memory_toast_queue: dict[str, list[dict[str, Any]]] = {}

    def __init__(self) -> None:
        self.cache_service = CacheService()
        self.redis = self.cache_service.client
        # Instâncias agora compartilham o estado estático acima

    def update_heartbeat(self, user_id: str) -> None:
        """Atualiza o timestamp do último sinal de vida do usuário."""
        # TTL = Threshold
        ttl = config.PRESENCE_OFFLINE_THRESHOLD_SECONDS

        # 1. Tenta Redis
        if self.redis:
            try:
                key = f"presence:{user_id}"
                self.redis.set(key, datetime.now().isoformat(), ex=ttl)
                return
            except Exception as e:
                logger.error(f"Falha ao setar heartbeat: {e}")

        # 2. Fallback Memória
        self._memory_last_seen[user_id] = datetime.now()

    def is_online(
        self,
        user_id: str,
        threshold_seconds: int = config.PRESENCE_OFFLINE_THRESHOLD_SECONDS,
    ) -> bool:
        """Verifica se o usuário esteve online recentemente."""
        # 1. Tenta Redis
        if self.redis:
            try:
                key = f"presence:{user_id}"
                # Simplesmente verifica se a chave existe (TTL cuida da expiração)
                return bool(self.redis.exists(key))
            except Exception as e:
                logger.error(f"Falha ao checar online: {e}")

        # 2. Fallback Memória
        last = self._memory_last_seen.get(user_id)
        if not last:
            return False

        delta = datetime.now() - last
        return delta.total_seconds() < threshold_seconds

    def push_toast(self, user_id: str, message: str, icon: str = "🔔") -> None:
        """Adiciona uma mensagem na fila de toasts."""
        payload = {
            "message": message,
            "icon": icon,
            "timestamp": datetime.now().isoformat(),
        }

        # 1. Tenta Redis (List)
        if self.redis:
            try:
                key = f"toasts:{user_id}"
                # Push no final da lista
                self.redis.rpush(key, json.dumps(payload))
                self.redis.expire(key, 86400)  # Expira fila em 24h se não lida
                return
            except Exception as e:
                logger.error(f"Falha ao pushar toast: {e}")

        # 2. Fallback Memória
        if user_id not in self._memory_toast_queue:
            self._memory_toast_queue[user_id] = []
        self._memory_toast_queue[user_id].append(payload)

    def pop_toasts(self, user_id: str) -> list[dict[str, Any]]:
        """Retorna e limpa a fila de toasts do usuário."""
        toasts = []

        # 1. Tenta Redis
        if self.redis:
            try:
                key = f"toasts:{user_id}"
                # LPOP para pegar todos (ou um lote grande)
                # Redis não tem "pop all" atômico simples, usamos lrange + delete ou pipeline
                # Para ser atômico: MULTI -> LRANGE -> DEL -> EXEC
                pipe = self.redis.pipeline()
                pipe.lrange(key, 0, -1)
                pipe.delete(key)
                results = pipe.execute()  # [lista_de_strings, count_deleted]

                raw_list = results[0]
                toasts = [json.loads(item) for item in raw_list]
                return toasts
            except Exception as e:
                logger.error(f"Falha ao popar toasts: {e}")
                # Se falhar o Redis, tenta entregar o que tem na memória?
                # Sim, pode ter algo lá se o redis caiu no meio.

        # 2. Fallback Memória
        toasts_mem = self._memory_toast_queue.get(user_id, [])
        self._memory_toast_queue[user_id] = []  # Limpa

        # Combina se necessário (raro)
        return toasts + toasts_mem
