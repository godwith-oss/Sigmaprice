"""Manual and automatic resolution of feedback comments"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sigmaprice.db.models import (
    FeedbackItem, FeedbackStatus, CatalogItem, User, UserRole,
)
from sigmaprice.core.exceptions import ValidationError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def resolve_auto(
    comment_id: int,
    session: Optional[Session] = None,
) -> bool:
    """
    Automatically resolve a comment (called when AI confidence >= 0.9).

    Only auto-fixes allowed fields:
    - name (typo corrections)
    - description
    - product_url
    - warranty_months

    Never auto-fixes: code, price, category.

    Returns True if resolved, False if manual review is needed.
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    fb = session.query(FeedbackItem).filter(
        FeedbackItem.id == comment_id
    ).first()
    if not fb:
        return False

    catalog_item = session.query(CatalogItem).filter(
        CatalogItem.id == fb.catalog_item_id
    ).first()
    if not catalog_item:
        return False

    fb.status = FeedbackStatus.AUTO_RESOLVED
    fb.auto_fixed = True
    fb.resolved_at = datetime.now(timezone.utc)
    session.commit()

    logger.info(f"Auto-resolved comment {comment_id}")
    return True


def resolve_manual(
    comment_id: int,
    admin_id: int,
    resolution: str,
    apply_fix: bool = True,
    session: Optional[Session] = None,
) -> FeedbackItem:
    """
    Manually resolve a comment by admin.

    Args:
        comment_id: Comment ID to resolve
        admin_id: Admin user ID (must have admin role)
        resolution: Admin's resolution notes
        apply_fix: Whether to apply the suggested fix

    Returns:
        Updated FeedbackItem

    Raises:
        ValidationError: If admin not found or not authorized
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    admin = session.query(User).filter(User.id == admin_id).first()
    if not admin or admin.role != UserRole.ADMIN:
        raise ValidationError("Only admin can manually resolve comments")

    fb = session.query(FeedbackItem).filter(
        FeedbackItem.id == comment_id
    ).first()
    if not fb:
        raise ValidationError(f"Comment {comment_id} not found")

    fb.admin_notes = resolution

    if apply_fix:
        fb.status = FeedbackStatus.RESOLVED
        _learn_from_admin(fb, resolution, session)
    else:
        fb.status = FeedbackStatus.REJECTED

    fb.resolved_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(fb)

    logger.info(
        f"Comment {comment_id} resolved by admin {admin_id}: "
        f"{'applied' if apply_fix else 'rejected'}"
    )
    return fb


def reject_comment(
    comment_id: int,
    admin_id: int,
    reason: str = "",
    session: Optional[Session] = None,
) -> FeedbackItem:
    """
    Reject a comment — mark as invalid/problem.

    Args:
        comment_id: Comment ID
        admin_id: Admin ID
        reason: Rejection reason

    Returns:
        Updated FeedbackItem
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    admin = session.query(User).filter(User.id == admin_id).first()
    if not admin or admin.role != UserRole.ADMIN:
        raise ValidationError("Only admin can reject comments")

    fb = session.query(FeedbackItem).filter(
        FeedbackItem.id == comment_id
    ).first()
    if not fb:
        raise ValidationError(f"Comment {comment_id} not found")

    fb.status = FeedbackStatus.REJECTED
    fb.admin_notes = reason or "Rejected by admin"
    fb.resolved_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(fb)

    logger.info(f"Comment {comment_id} rejected by admin {admin_id}")
    return fb


def _learn_from_admin(fb: FeedbackItem, resolution: str, session: Session) -> None:
    """Learn from admin's decision — add to knowledge base."""
    try:
        from sigmaprice.knowledge import add_rule
        from sigmaprice.db.models import KnowledgeBaseRuleType, KnowledgeBaseSource

        pattern = fb.comment.split()[:3]
        pattern = " ".join(p for p in pattern if len(p) >= 3)

        if pattern:
            add_rule(
                rule_type=KnowledgeBaseRuleType.EXCLUSION,
                pattern=pattern[:200],
                resolution="admin_resolved",
                source=KnowledgeBaseSource.ADMIN,
                confidence=1.0,
                session=session,
            )
    except Exception as e:
        logger.warning(f"Failed to learn from admin decision: {e}")
