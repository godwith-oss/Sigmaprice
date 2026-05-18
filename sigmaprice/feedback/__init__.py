"""Feedback module — user comments, AI analysis, auto/manual resolution"""
from sigmaprice.feedback.manager import (
    create_comment,
    get_comment,
    list_comments,
    get_pending_comments,
    get_analyzing_comments,
    update_comment_status,
)
from sigmaprice.feedback.analyzer import (
    analyze_comment,
)
from sigmaprice.feedback.resolver import (
    resolve_auto,
    resolve_manual,
    reject_comment,
)
from sigmaprice.feedback.reports import (
    generate_report,
    generate_summary,
)

__all__ = [
    "create_comment",
    "get_comment",
    "list_comments",
    "get_pending_comments",
    "get_analyzing_comments",
    "update_comment_status",
    "analyze_comment",
    "resolve_auto",
    "resolve_manual",
    "reject_comment",
    "generate_report",
    "generate_summary",
]
