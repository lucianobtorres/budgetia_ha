import json
from typing import Any

from core.embeddings.embedding_service import EmbeddingService
from core.logger import get_logger

from ..models.category import Category
from ..repositories.category_repository import ICategoryRepository

logger = get_logger("SemanticCategoryService")


class SemanticCategoryService:
    """
    Serviço que utiliza inteligência semântica para sugerir categorias.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        category_repo: ICategoryRepository,
        cache_service: Any | None = None,
    ):
        self._embedding_service = embedding_service
        self._category_repo = category_repo
        self._cache = cache_service
        self._category_vectors: list[tuple[Category, list[float]]] = []

    def refresh_category_map(self):
        """Atualiza o mapa de vetores das categorias atuais."""
        categories = self._category_repo.list_all()
        new_map = []

        for cat in categories:
            # Texto para embedding: Nome + Tags (se existirem)
            content = f"{cat.name} {cat.tags or ''}".strip()

            # Tenta buscar do cache primeiro
            vec = self._get_cached_vector(content, prefix="cat")
            if not vec:
                logger.info(f"Gerando novo embedding para categoria: {cat.name}")
                vec = self._embedding_service.get_embedding(content)
                self._cache_vector(content, vec, prefix="cat")

            if vec:
                new_map.append((cat, vec))

        self._category_vectors = new_map
        logger.info(
            f"Mapa semântico atualizado com {len(self._category_vectors)} categorias."
        )

    def suggest_category(
        self, description: str, transaction_type: str = "Despesa"
    ) -> Category | None:
        """Sugere a melhor categoria para uma descrição dada."""
        if not self._category_vectors:
            self.refresh_category_map()

        if not self._category_vectors:
            return None

        # Filtra categorias pelo tipo (Receita/Despesa)
        candidates = [
            cv for cv in self._category_vectors if cv[0].type == transaction_type
        ]
        if not candidates:
            return None

        # Tenta buscar embedding da descrição no cache (Optimization)
        target_vec = self._get_cached_vector(description, prefix="desc")

        if not target_vec:
            logger.debug(f"Cache miss para descrição: '{description}'. Chamando API...")
            target_vec = self._embedding_service.get_embedding(description)
            if target_vec:
                self._cache_vector(description, target_vec, prefix="desc")

        if not target_vec:
            return None

        # Encontra o melhor match
        best_cat = None
        max_sim = -1.0

        for cat, vec in candidates:
            sim = self._embedding_service.cosine_similarity(target_vec, vec)
            # Threshold de 0.35 para evitar associações muito loucas
            if sim > max_sim and sim > 0.35:
                max_sim = sim
                best_cat = cat

        if best_cat:
            logger.debug(
                f"Match Semântico: '{description}' -> '{best_cat.name}' (Sim: {max_sim:.4f})"
            )

        return best_cat

    def _get_cached_vector(self, text: str, prefix: str = "cat") -> list[float] | None:
        if not self._cache:
            return None
        try:
            key = f"emb:{prefix}:{text}"
            val = self._cache.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None

    def _cache_vector(self, text: str, vector: list[float], prefix: str = "cat"):
        if not self._cache or not vector:
            return
        try:
            key = f"emb:{prefix}:{text}"
            self._cache.set(key, json.dumps(vector), ex=86400 * 30)  # 30 dias para descrições
        except Exception:
            pass
