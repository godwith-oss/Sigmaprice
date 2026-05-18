"""Reports for admin on feedback processing"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sigmaprice.db.models import FeedbackItem, CatalogItem, User
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def generate_report(
    comment_id: int,
    session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Generate a detailed report for an admin about a processed comment.

    Contains:
    - Original comment text
    - What AI found on the web
    - What was fixed (or why not)
    - Which rule was created/updated
    - Processing date and time

    Returns:
        Report dict with keys: comment_id, user, item, original_comment,
        ai_result, resolution, status, timestamps
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    fb = session.query(FeedbackItem).filter(
        FeedbackItem.id == comment_id
    ).first()
    if not fb:
        return {"error": f"Comment {comment_id} not found"}

    user = session.query(User).filter(User.id == fb.user_id).first()
    catalog_item = session.query(CatalogItem).filter(
        CatalogItem.id == fb.catalog_item_id
    ).first()

    report = {
        "comment_id": fb.id,
        "user": {
            "id": user.id if user else None,
            "username": user.username if user else "deleted",
            "display_name": user.display_name if user else None,
        },
        "catalog_item": {
            "id": catalog_item.id if catalog_item else None,
            "code": catalog_item.code if catalog_item else None,
            "name": catalog_item.name if catalog_item else None,
        },
        "original_comment": fb.comment,
        "ai_resolution": fb.ai_resolution,
        "admin_notes": fb.admin_notes,
        "status": fb.status.value,
        "auto_fixed": fb.auto_fixed,
        "created_at": str(fb.created_at) if fb.created_at else None,
        "resolved_at": str(fb.resolved_at) if fb.resolved_at else None,
    }

    logger.info(f"Generated report for comment {comment_id}")
    return report


def generate_summary(
    session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Generate a summary of all feedback activity.

    Returns:
        dict with counts by status, total comments, auto-fix rate
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    total = session.query(FeedbackItem).count()
    auto_resolved = session.query(FeedbackItem).filter(
        FeedbackItem.status == "auto_resolved"
    ).count()
    manual_resolved = session.query(FeedbackItem).filter(
        FeedbackItem.status == "resolved"
    ).count()
    rejected = session.query(FeedbackItem).filter(
        FeedbackItem.status == "rejected"
    ).count()
    manual_required = session.query(FeedbackItem).filter(
        FeedbackItem.status == "manual_required"
    ).count()
    pending = session.query(FeedbackItem).filter(
        FeedbackItem.status == "pending"
    ).count()
    analyzing = session.query(FeedbackItem).filter(
        FeedbackItem.status == "analyzing"
    ).count()

    return {
        "total": total,
        "pending": pending,
        "analyzing": analyzing,
        "auto_resolved": auto_resolved,
        "manual_required": manual_required,
        "resolved": manual_resolved,
        "rejected": rejected,
        "auto_fix_rate": (
            auto_resolved / total if total > 0 else 0.0
        ),
    }
