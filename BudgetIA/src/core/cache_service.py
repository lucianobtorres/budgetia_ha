# Em: src/core/cache_service.py

import json

import pandas as pd
import redis

import config


from core.logger import get_logger

logger = get_logger("CacheService")

class CacheService:
    """
    Gerencia a conexão e as operações de cache com o Redis (Upstash).
    É especializado em serializar e desserializar dicionários de DataFrames.
    """

    def __init__(self, redis_url: str | None = config.UPSTASH_REDIS_URL):
        self.client: redis.Redis | None = None
        if redis_url:
            try:
                # 'decode_responses=True' faz o redis-py retornar strings (utf-8)
                self.client = redis.from_url(redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
                self.client.ping()
                logger.info("Conexão com o Cache Service (Redis/Upstash) bem-sucedida.")
            except redis.exceptions.ConnectionError as e:
                logger.warning(
                    f"Falha ao conectar ao Redis ({redis_url}). O cache será desabilitado. "
                    f"Verifique sua internet ou remova UPSTASH_REDIS_URL do .env se não quiser usar cache. (Detalhe: {e})"
                )
                self.client = None
        else:
            logger.warning("URL do Redis não configurada. O cache ficará desabilitado.")

    def _is_connected(self) -> bool:
        """Verifica se o cliente Redis está inicializado e conectado."""
        return self.client is not None

    def set_dfs(
        self, key: str, dfs_dict: dict[str, pd.DataFrame], timestamp: str | None
    ) -> None:
        """
        Serializa um dicionário de DataFrames para JSON e salva no Redis.
        'ex' é o tempo de expiração em segundos (default: 5 minutos).
        """
        if self.client is None:
            return

        try:
            # 1. Converte cada DataFrame para JSON (orient='split' preserva dtypes melhor)
            serialized_dfs = {
                aba_nome: df.to_json(orient="split", date_format="iso")
                for aba_nome, df in dfs_dict.items()
            }
            cache_payload = {
                "timestamp": timestamp,  # <-- Salva o timestamp
                "data": serialized_dfs,
            }
            json_string = json.dumps(cache_payload)

            # 3. Salva no Redis
            self.client.set(key, json_string)
            logger.debug(f"Cache SET para a chave '{key}' (Timestamp: {timestamp}).")

        except Exception as e:
            logger.error(f"ERRO ao serializar ou salvar DFs no cache: {e}")

    def get_dfs(self, key: str) -> tuple[dict[str, pd.DataFrame] | None, str | None]:
        """
        Busca uma string JSON do Redis e a desserializa para um dicionário de DataFrames.
        """
        if self.client is None:
            return None, None

        try:
            json_string = self.client.get(key)
            if json_string is None:
                logger.debug(f"Cache MISS para a chave '{key}'.")
                return None, None

            json_str: str = str(json_string)
            cache_payload = json.loads(json_str)
            serialized_dfs = cache_payload.get("data", {})
            cached_timestamp = cache_payload.get("timestamp")

            # 2. Desserializa os DFs
            from io import StringIO
            
            dfs_dict = {}
            for aba_nome, json_data in serialized_dfs.items():
                if json_data:
                    try:
                        # FIX: Wrap string in StringIO to avoid FutureWarning
                        dfs_dict[aba_nome] = pd.read_json(StringIO(json_data), orient="split")
                    except ValueError:
                        pass

            dfs_dict = self._ensure_dtypes(dfs_dict)

            logger.debug(f"Cache HIT para a chave '{key}'.")
            return dfs_dict, cached_timestamp

        except Exception as e:
            logger.error(f"ERRO ao ler ou desserializar DFs do cache: {e}")
            return None, None

    def delete(self, key: str) -> None:
        """Deleta uma chave do cache (invalidação)."""
        if self.client is None:
            return

        try:
            self.client.delete(key)
            logger.debug(f"Cache DELETED para a chave '{key}'.")
        except Exception as e:
            logger.error(f"ERRO ao deletar chave do cache: {e}")

    def _ensure_dtypes(
        self, dfs_dict: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
        """
        Garante que os DataFrames lidos do JSON tenham os dtypes corretos
        definidos no config.LAYOUT_DTYPES.
        """
        for aba_nome, dtypes in config.LAYOUT_DTYPES.items():
            if aba_nome in dfs_dict:
                df = dfs_dict[aba_nome]
                # Garante que colunas esperadas existam
                for col, dtype in dtypes.items():
                    if col not in df.columns:
                        df[col] = pd.NA

                # Aplica o dtype
                try:
                    df = df.astype(dtypes)
                    # Converte colunas de Data (definidas como 'str' no config) para datetime
                    if aba_nome == config.NomesAbas.TRANSACOES and "Data" in df.columns:
                        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

                    dfs_dict[aba_nome] = df
                except Exception as e:
                    logger.warning(
                        f"Não foi possível aplicar dtypes para a aba '{aba_nome}'. Erro: {e}"
                    )
        return dfs_dict

    # --- NOVO MÉTODO (RATE LIMITING) ---
    def check_rate_limit(
        self, action_key: str, limit: int, expire_seconds: int
    ) -> bool:
        """
        Verifica se uma ação (identificada pela chave) excedeu o limite.
        Retorna True se o limite foi excedido (bloquear), False caso contrário (permitir).
        """
        if self.client is None:
            # Se o cache estiver desabilitado, não podemos limitar
            return False

        try:
            # Pega o valor atual
            count = self.client.get(action_key)

            if count is None:
                # Primeira ação: define o contador como 1 e a expiração
                # 'pipeline' garante que as duas ações sejam atômicas
                p = self.client.pipeline()
                p.set(action_key, 1)
                p.expire(action_key, expire_seconds)
                p.execute()
                return False  # Permitido

            # Converte para int
            count_int = int(str(count))

            if count_int >= limit:
                # Limite atingido
                logger.warning(
                    f"Rate Limit atingido para a chave '{action_key}' (Limite: {limit})"
                )
                return True  # Bloquear

            # Ainda não atingiu, incrementa o contador
            self.client.incr(action_key)
            return False  # Permitido

        except Exception as e:
            logger.error(f"ERRO ao verificar Rate Limit: {e}")
            return False  # Falha aberta (permite a ação)
