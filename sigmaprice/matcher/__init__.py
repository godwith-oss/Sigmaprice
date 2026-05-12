"""Matcher module - товаросопоставление

Публичный интерфейс:
- match_item() - сопоставление товара из прайса с каталогом
- rebuild_all_embeddings() - пересчёт всех эмбеддингов
"""
from sigmaprice.matcher.matcher import match_item
from sigmaprice.matcher.rebuild_embeddings import rebuild_all_embeddings

__all__ = ['match_item', 'rebuild_all_embeddings']