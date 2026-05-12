"""Конфигурация Matcher модуля"""
from dataclasses import dataclass
from typing import Literal
from os import getenv


@dataclass
class MatcherConfig:
    """Конфигурация для модуля сопоставления товаров."""

    embedding_model: str = getenv('MATCHER_EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')

    embedding_threshold: float = float(getenv('MATCHER_EMBEDDING_THRESHOLD', '0.85'))

    web_research_provider: Literal['claude', 'openai', 'ollama', None] = getenv('MATCHER_WEB_PROVIDER', None)

    claude_api_key: str | None = getenv('CLAUDE_API_KEY')

    openai_api_key: str | None = getenv('OPENAI_API_KEY')

    ollama_url: str = getenv('OLLAMA_URL', 'http://localhost:11434')

    ollama_model: str = getenv('OLLAMA_MODEL', 'llama3')

    cache_web_research: bool = True

    cache_ttl_days: int = 30


DEFAULT_CONFIG = MatcherConfig()