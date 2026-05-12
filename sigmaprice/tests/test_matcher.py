"""Тесты для модуля Matcher"""
import pytest
import json
from decimal import Decimal

from sigmaprice.core.types import RawItem, AvailabilityStatus
from sigmaprice.matcher.config import MatcherConfig
from sigmaprice.matcher.matcher import _cosine_similarity


class TestCosineSimilarity:
    """Тесты функции косинусного сходства."""

    def test_identical_vectors(self):
        vec = [1.0, 0.0, 0.0]
        assert _cosine_similarity(vec, vec) == 1.0

    def test_orthogonal_vectors(self):
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        assert _cosine_similarity(vec1, vec2) == 0.0

    def test_opposite_vectors(self):
        vec = [1.0, 0.0, 0.0]
        assert _cosine_similarity(vec, [-1.0, 0.0, 0.0]) == -1.0

    def test_zero_vector(self):
        vec = [1.0, 0.0, 0.0]
        zero = [0.0, 0.0, 0.0]
        assert _cosine_similarity(vec, zero) == 0.0


class TestMatcherConfig:
    """Тесты конфигурации."""

    def test_default_config(self):
        config = MatcherConfig()
        assert config.embedding_model == "paraphrase-multilingual-MiniLM-L12-v2"
        assert config.embedding_threshold == 0.85
        assert config.web_research_provider is None

    def test_custom_config(self):
        config = MatcherConfig(
            embedding_model="all-MiniLM-L6-v2",
            embedding_threshold=0.9,
            web_research_provider="claude",
            claude_api_key="test-key"
        )
        assert config.embedding_model == "all-MiniLM-L6-v2"
        assert config.embedding_threshold == 0.9
        assert config.web_research_provider == "claude"

    def test_env_variables(self, monkeypatch):
        monkeypatch.setenv("MATCHER_EMBEDDING_MODEL", "test-model")
        monkeypatch.setenv("MATCHER_EMBEDDING_THRESHOLD", "0.8")
        monkeypatch.setenv("MATCHER_WEB_PROVIDER", "openai")

        config = MatcherConfig()
        assert config.embedding_model == "test-model"
        assert config.embedding_threshold == 0.8
        assert config.web_research_provider == "openai"


class TestMatchResult:
    """Тесты структуры результата сопоставления."""
    from sigmaprice.matcher.matcher import MatchResult

    def test_match_result_creation(self):
        result = MatchResult(
            catalog_item_id=123,
            confidence=0.95,
            method="article_match",
            is_new=False
        )
        assert result.catalog_item_id == 123
        assert result.confidence == 0.95
        assert result.method == "article_match"
        assert result.is_new is False

    def test_match_result_new_item(self):
        result = MatchResult(
            catalog_item_id=None,
            confidence=0.0,
            method="not_matched",
            is_new=True
        )
        assert result.catalog_item_id is None
        assert result.is_new is True


class TestEmbeddingProvider:
    """Тесты провайдера эмбеддингов."""

    def test_sentence_transformer_provider_init(self):
        from sigmaprice.matcher.embedding_provider import SentenceTransformerProvider

        provider = SentenceTransformerProvider("paraphrase-multilingual-MiniLM-L12-v2")
        assert provider.get_dimension() == 384

    def test_generate_embedding(self):
        from sigmaprice.matcher.embedding_provider import SentenceTransformerProvider

        provider = SentenceTransformerProvider("paraphrase-multilingual-MiniLM-L12-v2")
        embedding = provider.generate("Видеокарта NVIDIA RTX 5080")

        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_generate_empty_text(self):
        from sigmaprice.matcher.embedding_provider import SentenceTransformerProvider

        provider = SentenceTransformerProvider("paraphrase-multilingual-MiniLM-L12-v2")
        embedding = provider.generate("")

        assert len(embedding) == 384
        assert all(x == 0.0 for x in embedding)


class TestFactory:
    """Тесты фабрики провайдеров."""

    def test_get_embedding_provider(self):
        from sigmaprice.matcher.factory import get_embedding_provider

        provider = get_embedding_provider(MatcherConfig())
        assert provider.get_dimension() == 384

    def test_get_web_research_provider_none(self):
        from sigmaprice.matcher.factory import get_web_research_provider

        config = MatcherConfig(web_research_provider=None)
        provider = get_web_research_provider(config)
        assert provider is None

    def test_get_web_research_provider_claude_no_key(self):
        from sigmaprice.matcher.factory import get_web_research_provider

        config = MatcherConfig(web_research_provider="claude", claude_api_key=None)
        with pytest.raises(ValueError, match="CLAUDE_API_KEY не настроен"):
            get_web_research_provider(config)

    def test_get_web_research_provider_openai_no_key(self):
        from sigmaprice.matcher.factory import get_web_research_provider

        config = MatcherConfig(web_research_provider="openai", openai_api_key=None)
        with pytest.raises(ValueError, match="OPENAI_API_KEY не настроен"):
            get_web_research_provider(config)


class TestRebuildEmbeddings:
    """Тесты пересчёта эмбеддингов."""

    def test_rebuild_function_imports(self):
        from sigmaprice.matcher import rebuild_all_embeddings
        assert callable(rebuild_all_embeddings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])