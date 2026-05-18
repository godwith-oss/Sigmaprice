"""Matcher module - товаросопоставление

Публичный интерфейс:
- match_item() - сопоставление товара из прайса с каталогом
- research_item() - веб-поиск для проверки комментариев (Module 9)
- rebuild_all_embeddings() - пересчёт всех эмбеддингов
"""
from sigmaprice.matcher.matcher import match_item, research_item
from sigmaprice.matcher.rebuild_embeddings import rebuild_all_embeddings
from sigmaprice.matcher.factory import get_web_research_provider

__all__ = [
    'match_item',
    'research_item',
    'rebuild_all_embeddings',
    'get_web_research_provider',
]