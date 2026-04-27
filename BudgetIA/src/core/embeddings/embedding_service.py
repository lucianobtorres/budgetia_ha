# src/core/embeddings/embedding_service.py

import numpy as np
from openai import OpenAI

import config
from core.logger import get_logger

logger = get_logger("EmbeddingService")


class EmbeddingService:
    """
    Serviço para geração e comparação de Embeddings (vetores semânticos).
    Essencial para categorização inteligente e busca por similaridade.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.OPENAI_API_KEY
        # Prioriza a chave paga se disponível
        self.gemini_key = config.GEMINI_API_KEY_PAID or config.GOOGLE_API_KEY

        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "text-embedding-3-small"

    def get_embedding(self, text: str) -> list[float]:
        """Gera o embedding para um texto (Tenta OpenAI, fallback para Gemini)."""
        if not text or not isinstance(text, str):
            return []

        # 1. Tenta OpenAI
        if self.client and self.api_key:
            try:
                text = text.replace("\n", " ").strip()
                response = self.client.embeddings.create(input=[text], model=self.model)
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"Erro no OpenAI Embedding, tentando Gemini: {e}")

        # 2. Fallback para Gemini (Via LangChain para evitar conflitos)
        if self.gemini_key:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings

                gemini_embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-2",
                    google_api_key=self.gemini_key,
                    task_type="retrieval_query",
                )
                return gemini_embeddings.embed_query(text)
            except Exception as e:
                logger.error(
                    f"Erro fatal ao gerar embedding no Gemini (LangChain): {e}"
                )

        return []

    def cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """Calcula a similaridade de cosseno entre dois vetores."""
        if not v1 or not v2:
            return 0.0

        vec1 = np.array(v1)
        vec2 = np.array(v2)

        dot_product = np.dot(vec1, vec2)
        norm_v1 = np.linalg.norm(vec1)
        norm_v2 = np.linalg.norm(vec2)

        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0

        return float(dot_product / (norm_v1 * norm_v2))

    def find_best_match(
        self, target_vec: list[float], candidate_vecs: list[list[float]]
    ) -> int:
        """Retorna o índice do candidato mais similar ao alvo."""
        if not target_vec or not candidate_vecs:
            return -1

        similarities = [self.cosine_similarity(target_vec, v) for v in candidate_vecs]
        return int(np.argmax(similarities))
