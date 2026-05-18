"""Модуль сопоставления товаров - основная логика"""
import json
from dataclasses import dataclass

from sigmaprice.core.types import RawItem
from sigmaprice.core.logger import get_logger
from sigmaprice.core.database import get_session
from sigmaprice.db.models import (
    CatalogItem, SupplierItemMapping, ItemEmbedding
)
from sigmaprice.matcher.config import MatcherConfig, DEFAULT_CONFIG
from sigmaprice.matcher.factory import get_embedding_provider, get_web_research_provider

logger = get_logger(__name__)


@dataclass
class MatchResult:
    """Результат сопоставления товара."""
    catalog_item_id: int | None
    confidence: float
    method: str
    is_new: bool


def match_item(item: RawItem, supplier_id: int, config: MatcherConfig | None = None) -> MatchResult:
    """
    Сопоставляет товар из прайса с каталогом.

    Алгоритм (5 уровней):
    1. Правила - нормализация, синонимы, словарь суффиксов
    2. Атрибуты - точное совпадение по артикулу, EAN
    3. ИИ локально - семантическое сравнение через эмбеддинги
    4. ИИ + интернет - веб-поиск для сложных случаев
    5. Очередь на проверку админу
    """
    if config is None:
        config = DEFAULT_CONFIG

    session = get_session()

    existing_mapping = session.query(SupplierItemMapping).filter(
        SupplierItemMapping.supplier_id == supplier_id,
        SupplierItemMapping.supplier_code == item.supplier_code
    ).first()

    if existing_mapping:
        return MatchResult(
            catalog_item_id=existing_mapping.catalog_item_id,
            confidence=1.0,
            method="exact_code_match",
            is_new=False
        )

    result = _match_by_attributes(item, session)
    if result:
        return result

    result = _match_by_embedding(item, session, config)
    if result:
        return result

    result = _match_by_web_research(item, session, config)
    if result:
        return result

    return MatchResult(
        catalog_item_id=None,
        confidence=0.0,
        method="not_matched",
        is_new=True
    )


def _match_by_attributes(item: RawItem, session) -> MatchResult | None:
    """Уровень 2: Точное совпадение по атрибутам."""
    if item.article:
        catalog_item = session.query(CatalogItem).filter(
            CatalogItem.article == item.article
        ).first()
        if catalog_item:
            _save_mapping(session, catalog_item.id, item.supplier_id, item.supplier_code)
            return MatchResult(
                catalog_item_id=catalog_item.id,
                confidence=1.0,
                method="article_match",
                is_new=False
            )

    if item.ean:
        catalog_item = session.query(CatalogItem).filter(
            CatalogItem.ean == item.ean
        ).first()
        if catalog_item:
            _save_mapping(session, catalog_item.id, item.supplier_id, item.supplier_code)
            return MatchResult(
                catalog_item_id=catalog_item.id,
                confidence=0.95,
                method="ean_match",
                is_new=False
            )
    return None


def _match_by_embedding(item: RawItem, session, config: MatcherConfig) -> MatchResult | None:
    """Уровень 3: Семантическое сравнение через эмбеддинги."""
    provider = get_embedding_provider(config)
    item_embedding = provider.generate(item.name)

    all_embeddings = session.query(ItemEmbedding).all()

    best_match = None
    best_similarity = 0.0

    for emb_record in all_embeddings:
        if emb_record.catalog_item_id is None:
            continue
        stored_embedding = json.loads(emb_record.embedding)
        similarity = _cosine_similarity(item_embedding, stored_embedding)

        if similarity > best_similarity and similarity >= config.embedding_threshold:
            best_similarity = similarity
            best_match = emb_record.catalog_item

    if best_match:
        _save_mapping(session, best_match.id, item.supplier_id, item.supplier_code)
        return MatchResult(
            catalog_item_id=best_match.id,
            confidence=best_similarity,
            method="embedding_match",
            is_new=False
        )
    return None


def _match_by_web_research(item: RawItem, session, config: MatcherConfig) -> MatchResult | None:
    """Уровень 4: Веб-поиск для сложных случаев."""
    provider = get_web_research_provider(config)
    if provider is None:
        return None

    query = (
        f"Товар: {item.name}. "
        f"Производитель: {item.manufacturer or 'неизвестен'}. "
    )
    if item.article:
        query += f"Артикул: {item.article}. "

    try:
        result = provider.research(item, query)
        if result.get("found") and result.get("confidence", 0) >= 0.7:
            info = result.get("info", "")
            model_match = _extract_model_from_research(info, item.name)

            if model_match:
                catalog_item = session.query(CatalogItem).filter(
                    CatalogItem.name.ilike(f"%{model_match}%")
                ).first()
                if catalog_item:
                    _save_mapping(session, catalog_item.id, item.supplier_id, item.supplier_code)
                    return MatchResult(
                        catalog_item_id=catalog_item.id,
                        confidence=result.get("confidence", 0.8),
                        method="web_research_match",
                        is_new=False
                    )

        if result.get("found"):
            logger.info(
                f"Web research for '{item.name}': found but no catalog match. "
                f"Confidence: {result.get('confidence')}"
            )

    except Exception as e:
        logger.error(f"Web research error for '{item.name}': {e}")

    return None


def research_item(item_name: str, query: str, config: MatcherConfig | None = None) -> dict:
    """
    Research an item on the web using configured provider.
    Used by Module 9 (feedback) to verify user comments.
    """
    if config is None:
        config = DEFAULT_CONFIG

    provider = get_web_research_provider(config)
    if provider is None:
        return {"found": False, "info": "Web research provider not configured", "confidence": 0.0}

    dummy_item = RawItem(
        supplier_id=0,
        supplier_code="",
        name=item_name,
        description="",
        price=0,
        currency="RUB",
        availability="in_stock",
        quantity=None,
        warranty_months=None,
        article=None,
        ean=None,
        manufacturer=None,
        delivery_type=None,
    )

    return provider.research(dummy_item, query)


def _extract_model_from_research(research_info: str, item_name: str) -> str | None:
    """Extract potential model name from web research results."""
    import re

    if not research_info:
        return None

    for word in item_name.split():
        if len(word) >= 4 and word.isalnum():
            if word in research_info:
                return word

    rtx_pattern = r'(RTX\s*\d{4}\s*(Ti|SUPER)?)'
    match = re.search(rtx_pattern, research_info, re.IGNORECASE)
    if match:
        return match.group(0)

    return None


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Косинусное сходство между векторами."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = sum(a * a for a in vec1) ** 0.5
    mag2 = sum(b * b for b in vec2) ** 0.5
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def _save_mapping(session, catalog_item_id: int, supplier_id: int, supplier_code: str):
    """Сохраняет соответствие кода поставщика и товара каталога."""
    mapping = SupplierItemMapping(
        catalog_item_id=catalog_item_id,
        supplier_id=supplier_id,
        supplier_code=supplier_code
    )
    session.add(mapping)
    session.commit()


def search_similar_items(catalog_item_id: int, limit: int = 10, config: MatcherConfig | None = None):
    """Поиск похожих товаров в каталоге."""
    if config is None:
        config = DEFAULT_CONFIG

    session = get_session()

    item_emb = session.query(ItemEmbedding).filter(
        ItemEmbedding.catalog_item_id == catalog_item_id
    ).first()
    if not item_emb:
        return []

    provider = get_embedding_provider(config)
    query_embedding = json.loads(item_emb.embedding)

    all_embeddings = session.query(ItemEmbedding).filter(
        ItemEmbedding.catalog_item_id != catalog_item_id
    ).all()

    similarities = []
    for emb in all_embeddings:
        stored = json.loads(emb.embedding)
        sim = _cosine_similarity(query_embedding, stored)
        similarities.append((emb.catalog_item, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:limit]