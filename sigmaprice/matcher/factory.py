"""Фабрика провайдеров для Matcher"""
from sigmaprice.matcher.config import MatcherConfig
from sigmaprice.matcher.providers import EmbeddingProvider, WebResearchProvider
from sigmaprice.matcher.embedding_provider import SentenceTransformerProvider
from sigmaprice.matcher.web_providers import (
    ClaudeResearchProvider,
    OpenAIResearchProvider,
    OllamaResearchProvider
)
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def get_embedding_provider(config: MatcherConfig | None = None) -> EmbeddingProvider:
    """Создаёт провайдер эмбеддингов."""
    if config is None:
        from sigmaprice.matcher.config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG
    return SentenceTransformerProvider(config.embedding_model)


def get_web_research_provider(config: MatcherConfig | None = None) -> WebResearchProvider | None:
    """Создаёт провайдер веб-поиска или None если отключён."""
    if config is None:
        from sigmaprice.matcher.config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG

    provider = config.web_research_provider

    if provider is None:
        logger.info("Веб-поиск отключён")
        return None

    if provider == 'claude':
        if not config.claude_api_key:
            raise ValueError("CLAUDE_API_KEY не настроен")
        return ClaudeResearchProvider(config.claude_api_key)

    elif provider == 'openai':
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY не настроен")
        return OpenAIResearchProvider(config.openai_api_key)

    elif provider == 'ollama':
        return OllamaResearchProvider(config.ollama_url, config.ollama_model)

    else:
        raise ValueError(f"Неизвестный провайдер веб-поиска: {provider}")