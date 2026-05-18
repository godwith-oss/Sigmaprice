"""Feedback comment CRUD operations"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sigmaprice.db.models import (
    FeedbackItem, FeedbackStatus, User, UserRole, CatalogItem
)
from sigmaprice.core.exceptions import ValidationError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def create_comment(
    user_id: int,
    catalog_item_id: int,
    comment: str,
    session: Optional[Session] = None,
) -> FeedbackItem:
    """
    Create a feedback comment about a catalog item error.

    Access: trusted_user or admin only (checked via Module 8).

    Args:
        user_id: ID of user leaving comment
        catalog_item_id: ID of catalog item
        comment: Comment text

    Returns:
        Created FeedbackItem

    Raises:
        ValidationError: If user doesn't have comment rights
        ValidationError: If catalog item not found
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValidationError(f"User {user_id} not found")

    if not user.is_active:
        raise ValidationError("Inactive user cannot leave comments")

    if user.role not in (UserRole.ADMIN, UserRole.TRUSTED_USER):
        raise ValidationError(
            f"User role '{user.role.value}' cannot leave comments. "
            "Required: trusted_user or admin"
        )

    item = session.query(CatalogItem).filter(
        CatalogItem.id == catalog_item_id
    ).first()
    if not item:
        raise ValidationError(f"Catalog item {catalog_item_id} not found")

    if not comment or not comment.strip():
        raise ValidationError("Comment cannot be empty")

    feedback = FeedbackItem(
        user_id=user_id,
        catalog_item_id=catalog_item_id,
        comment=comment.strip(),
        status=FeedbackStatus.PENDING,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)

    logger.info(
        f"Comment created: user={user_id}, item={catalog_item_id}, "
        f"id={feedback.id}"
    )
    return feedback


def get_comment(
    comment_id: int,
    session: Optional[Session] = None,
) -> Optional[FeedbackItem]:
    """Get comment by ID."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(FeedbackItem).filter(
        FeedbackItem.id == comment_id
    ).first()


def list_comments(
    filters: Optional[Dict[str, Any]] = None,
    session: Optional[Session] = None,
) -> List[FeedbackItem]:
    """
    List comments with optional filters.

    Supported filters:
        status: FeedbackStatus
        user_id: int
        catalog_item_id: int
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    query = session.query(FeedbackItem)

    if filters:
        if "status" in filters:
            query = query.filter(FeedbackItem.status == filters["status"])
        if "user_id" in filters:
            query = query.filter(FeedbackItem.user_id == filters["user_id"])
        if "catalog_item_id" in filters:
            query = query.filter(
                FeedbackItem.catalog_item_id == filters["catalog_item_id"]
            )

    return query.order_by(FeedbackItem.created_at.desc()).all()


def get_pending_comments(
    session: Optional[Session] = None,
) -> List[FeedbackItem]:
    """Get comments requiring admin attention (manual_required)."""
    return list_comments(
        filters={"status": FeedbackStatus.MANUAL_REQUIRED},
        session=session,
    )


def get_analyzing_comments(
    session: Optional[Session] = None,
) -> List[FeedbackItem]:
    """Get comments that are newly created and need analysis (pending)."""
    return list_comments(
        filters={"status": FeedbackStatus.PENDING},
        session=session,
    )


def update_comment_status(
    comment_id: int,
    status: FeedbackStatus,
    ai_resolution: Optional[str] = None,
    admin_notes: Optional[str] = None,
    auto_fixed: bool = False,
    session: Optional[Session] = None,
) -> FeedbackItem:
    """Update comment status and resolution fields."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    fb = session.query(FeedbackItem).filter(
        FeedbackItem.id == comment_id
    ).first()
    if not fb:
        raise ValidationError(f"Comment {comment_id} not found")

    fb.status = status
    if ai_resolution is not None:
        fb.ai_resolution = ai_resolution
    if admin_notes is not None:
        fb.admin_notes = admin_notes
    if auto_fixed:
        fb.auto_fixed = True

    if status in (FeedbackStatus.RESOLVED, FeedbackStatus.REJECTED):
        fb.resolved_at = datetime.now(timezone.utc)

    session.commit()
    session.refresh(fb)

    logger.info(f"Comment {comment_id} status -> {status.value}")
    return fb
