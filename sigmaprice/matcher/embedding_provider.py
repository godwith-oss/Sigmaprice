"""Провайдер эмбеддингов на базе sentence-transformers"""
from sigmaprice.matcher.providers import EmbeddingProvider
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


class SentenceTransformerProvider(EmbeddingProvider):
    """Провайдер эмбеддингов через sentence-transformers."""

    def __init__(self, model_name: str):
        """Инициализирует модель sentence-transformers."""
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Загружена модель эмбеддингов: {model_name}, dimension={self.dimension}")

    def generate(self, text: str) -> list[float]:
        """Генерирует эмбеддинг для текста."""
        if not text or not text.strip():
            return [0.0] * self.dimension
        embedding = self.model.encode(text.strip())
        return embedding.tolist()

    def get_dimension(self) -> int:
        """Возвращает размерность вектора."""
        return self.dimension