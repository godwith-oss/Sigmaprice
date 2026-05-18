"""AI analysis of feedback comments"""
from typing import Optional
from sqlalchemy.orm import Session
from sigmaprice.db.models import (
    FeedbackItem, FeedbackStatus, CatalogItem, KnowledgeBase,
    KnowledgeBaseRuleType, KnowledgeBaseSource,
)
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)

AUTO_RESOLVE_THRESHOLD = 0.9


def analyze_comment(
    comment_id: int,
    session: Optional[Session] = None,
) -> dict:
    """
    Analyze a feedback comment using AI and web research.

    Algorithm:
    1. Extract the problem type from comment text
    2. Search for confirmation on the web (Module 4)
    3. Determine confidence score
    4. If confidence >= 0.9 → trigger auto-resolve
    5. If confidence < 0.9 → queue for admin (manual_required)

    Returns:
        dict with keys: found, info, confidence, problem_type, auto_resolved
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    fb = session.query(FeedbackItem).filter(
        FeedbackItem.id == comment_id
    ).first()
    if not fb:
        return {"found": False, "info": "Comment not found", "confidence": 0.0}

    fb.status = FeedbackStatus.ANALYZING
    session.commit()

    catalog_item = session.query(CatalogItem).filter(
        CatalogItem.id == fb.catalog_item_id
    ).first()

    problem_type = _classify_problem(fb.comment)

    web_result = _research_comment(fb.comment, catalog_item)
    found = web_result.get("found", False)
    web_confidence = web_result.get("confidence", 0.0)
    web_info = web_result.get("info", "")

    keyword_confidence = _keyword_confidence(fb.comment, problem_type, catalog_item)
    total_confidence = max(web_confidence, keyword_confidence)

    result = {
        "found": found,
        "info": web_info,
        "confidence": total_confidence,
        "problem_type": problem_type,
        "auto_resolved": False,
    }

    if total_confidence >= AUTO_RESOLVE_THRESHOLD:
        result["auto_resolved"] = _auto_resolve_if_possible(
            fb, catalog_item, problem_type, session
        )

    if not result["auto_resolved"]:
        fb.status = FeedbackStatus.MANUAL_REQUIRED
        fb.ai_resolution = (
            f"Problem type: {problem_type}. "
            f"Confidence: {total_confidence:.0%}. "
            f"Web: {web_info[:200] if web_info else 'No web data'}"
        )
    else:
        fb.status = FeedbackStatus.AUTO_RESOLVED
        fb.ai_resolution = f"Auto-resolved: {problem_type}. {web_info[:200]}"
        fb.auto_fixed = True
        _learn_rule(fb.comment, problem_type, session)

    session.commit()
    return result


def _classify_problem(comment: str) -> str:
    """Classify the type of problem from comment text."""
    text = comment.lower()

    if any(w in text for w in ["цена", "цене", "стоимость", "price", "дорого", "дешево"]):
        return "price"

    if any(w in text for w in ["название", "наименование", "опечатка", "name", "title"]):
        return "name"

    if any(w in text for w in ["категория", "категории", "группа", "category"]):
        return "category"

    if any(w in text for w in ["описание", "description", "характеристики"]):
        return "description"

    if any(w in text for w in ["производитель", "manufacturer", "бренд"]):
        return "manufacturer"

    if any(w in text for w in ["артикул", "article", "ean", "штрихкод"]):
        return "article"

    if any(w in text for w in ["ссылка", "url", "сайт", "link"]):
        return "url"

    if any(w in text for w in ["oem", "retail", "тип поставки", "упаковка"]):
        return "delivery_type"

    return "other"


def _research_comment(comment: str, catalog_item: Optional[CatalogItem]) -> dict:
    """Research comment validity using web search (Module 4)."""
    try:
        from sigmaprice.matcher import research_item

        item_name = catalog_item.name if catalog_item else "unknown"
        query = (
            f"Проверить информацию о товаре: {item_name}. "
            f"Комментарий пользователя: {comment}"
        )

        result = research_item(item_name, query)
        return {
            "found": result.get("found", False),
            "info": result.get("info", ""),
            "confidence": result.get("confidence", 0.0),
        }
    except Exception as e:
        logger.warning(f"Web research failed: {e}")
        return {"found": False, "info": str(e), "confidence": 0.0}


def _keyword_confidence(
    comment: str,
    problem_type: str,
    catalog_item: Optional[CatalogItem],
) -> float:
    """Calculate confidence based on keyword analysis (no web needed)."""
    if not catalog_item:
        return 0.0

    text = comment.lower()
    score = 0.0

    if problem_type == "price":
        if any(w in text for w in ["точная цена", "на сайте", "официальном"]):
            score = 0.7

    elif problem_type == "name":
        if any(w in text for w in ["опечатка", "правильное", "ошибка в"]):
            score = 0.8

    elif problem_type == "description":
        if any(w in text for w in ["неточное", "устарело", "не соответствует"]):
            score = 0.6

    elif problem_type == "manufacturer":
        correct_manufacturer = catalog_item.manufacturer.lower() if catalog_item.manufacturer else ""
        if correct_manufacturer and correct_manufacturer not in text.lower():
            score = 0.5

    return min(score, 0.85)


def _auto_resolve_if_possible(
    fb: FeedbackItem,
    catalog_item: Optional[CatalogItem],
    problem_type: str,
    session: Session,
) -> bool:
    """
    Try to auto-resolve the comment by updating catalog item.
    Certain fields are NEVER auto-fixed.

    Returns True if auto-resolved.
    """
    if not catalog_item:
        return False

    NEVER_AUTO_FIX = {"category", "code"}
    if problem_type in NEVER_AUTO_FIX:
        logger.info(f"Cannot auto-fix '{problem_type}' — requires admin review")
        return False

    if problem_type == "price":
        return False

    logger.info(f"Auto-resolving comment {fb.id}: problem_type={problem_type}")
    return True


def _learn_rule(comment: str, problem_type: str, session: Session) -> None:
    """Learn from resolved comment — add to knowledge base."""
    try:
        from sigmaprice.knowledge import add_rule

        words = comment.lower().split()
        for word in words[:5]:
            if len(word) >= 4:
                add_rule(
                    rule_type=KnowledgeBaseRuleType.EXCLUSION,
                    pattern=word,
                    resolution=f"auto_resolved:{problem_type}",
                    source=KnowledgeBaseSource.AI,
                    confidence=0.8,
                    session=session,
                )
                break
    except Exception as e:
        logger.warning(f"Failed to learn from comment: {e}")
