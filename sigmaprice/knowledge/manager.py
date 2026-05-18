"""Knowledge base manager — learned rules for AI matching and cataloging

Stores exclusion patterns, suffix dictionaries, and synonym mappings
that the AI learns from admin corrections and manual input.

Table: knowledge_base
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sigmaprice.db.models import KnowledgeBase, KnowledgeBaseRuleType, KnowledgeBaseSource
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)

EXCLUDED_DELIVERY_KEYWORDS = {
    "поврежденная упаковка",
    "повреждённая упаковка",
    "damaged packaging",
    "damaged box",
    "утс",
    "битая упаковка",
}

SUFFIX_EXAMPLES = {
    "SHADOW 3X": "SHADOW 3X OC",
    "VENTUS 2X": "VENTUS 2X OC",
    "GAMING X": "GAMING X TRIO",
    "WINDFORCE": "WINDFORCE OC",
    "EAGLE": "EAGLE OC",
    "PULSE": "PULSE OC",
}

SYNONYM_EXAMPLES = {
    "BOX": "Retail",
    "RTL": "Retail",
    "RET": "Retail",
    "TRAY": "OEM",
    "MPK": "OEM",
}


def add_rule(
    rule_type: KnowledgeBaseRuleType,
    pattern: str,
    resolution: str,
    source: KnowledgeBaseSource = KnowledgeBaseSource.ADMIN,
    confidence: float = 1.0,
    session: Optional[Session] = None,
) -> KnowledgeBase:
    """Add a new knowledge base rule."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    rule = KnowledgeBase(
        rule_type=rule_type,
        pattern=pattern,
        resolution=resolution,
        source=source,
        confidence=confidence,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)

    logger.debug(f"Added KB rule: [{rule_type.value}] {pattern} -> {resolution}")
    return rule


def get_rules(
    rule_type: KnowledgeBaseRuleType,
    session: Optional[Session] = None,
) -> List[KnowledgeBase]:
    """Get all rules of a specific type, ordered by confidence desc."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return (
        session.query(KnowledgeBase)
        .filter(KnowledgeBase.rule_type == rule_type)
        .order_by(KnowledgeBase.confidence.desc())
        .all()
    )


def get_patterns_by_type(
    rule_type: KnowledgeBaseRuleType,
    session: Optional[Session] = None,
) -> List[str]:
    """Get just the pattern strings for a rule type."""
    rules = get_rules(rule_type, session)
    return [r.pattern for r in rules]


def is_excluded_by_kb(
    text: str,
    session: Optional[Session] = None,
) -> bool:
    """
    Check if text matches any EXCLUSION pattern in the knowledge base.

    Used to filter out items with damaged/defective packaging
    and other quality-related exclusions.
    """
    patterns = get_patterns_by_type(KnowledgeBaseRuleType.EXCLUSION, session)
    text_lower = text.lower()
    for pattern in patterns:
        if pattern.lower() in text_lower:
            return True
    return False


def get_suffixes(
    session: Optional[Session] = None,
) -> dict:
    """Get suffix dictionary for distinguishing similar models."""
    rules = get_rules(KnowledgeBaseRuleType.SUFFIX, session)
    return {r.pattern: r.resolution for r in rules}


def get_synonyms(
    session: Optional[Session] = None,
) -> dict:
    """Get synonym mapping (e.g. BOX -> Retail, TRAY -> OEM)."""
    rules = get_rules(KnowledgeBaseRuleType.SYNONYM, session)
    return {r.pattern: r.resolution for r in rules}


def seed_default_rules(session: Optional[Session] = None) -> int:
    """
    Populate knowledge base with default rules if empty.
    Safe to call multiple times — skips existing entries.

    Returns number of rules added.
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    existing = session.query(KnowledgeBase).count()
    if existing > 0:
        logger.info(f"Knowledge base already has {existing} rules, skipping seed")
        return 0

    count = 0

    for keyword in EXCLUDED_DELIVERY_KEYWORDS:
        add_rule(
            rule_type=KnowledgeBaseRuleType.EXCLUSION,
            pattern=keyword,
            resolution="exclude",
            source=KnowledgeBaseSource.ADMIN,
            confidence=1.0,
            session=session,
        )
        count += 1

    for pattern, resolution in SUFFIX_EXAMPLES.items():
        add_rule(
            rule_type=KnowledgeBaseRuleType.SUFFIX,
            pattern=pattern,
            resolution=resolution,
            source=KnowledgeBaseSource.ADMIN,
            confidence=0.9,
            session=session,
        )
        count += 1

    for pattern, resolution in SYNONYM_EXAMPLES.items():
        add_rule(
            rule_type=KnowledgeBaseRuleType.SYNONYM,
            pattern=pattern,
            resolution=resolution,
            source=KnowledgeBaseSource.ADMIN,
            confidence=1.0,
            session=session,
        )
        count += 1

    logger.info(f"Seeded {count} default rules into knowledge base")
    return count


def delete_rule(
    rule_id: int,
    session: Optional[Session] = None,
) -> bool:
    """Delete a knowledge base rule by ID."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    rule = session.query(KnowledgeBase).filter(KnowledgeBase.id == rule_id).first()
    if not rule:
        return False

    session.delete(rule)
    session.commit()
    logger.info(f"Deleted KB rule: [{rule.rule_type.value}] {rule.pattern}")
    return True
