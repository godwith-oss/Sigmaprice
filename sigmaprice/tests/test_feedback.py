"""Tests for Module 9 - Feedback"""
import pytest
from unittest.mock import MagicMock, patch
from sigmaprice.feedback import (
    create_comment,
    get_comment,
    list_comments,
    get_pending_comments,
    analyze_comment,
    resolve_auto,
    resolve_manual,
    reject_comment,
    generate_report,
    generate_summary,
)
from sigmaprice.db.models import FeedbackStatus, UserRole
from sigmaprice.core.exceptions import ValidationError


class TestCommentCRUD:
    """Test comment creation and retrieval."""

    @patch('sigmaprice.core.database.get_session')
    def test_create_comment_trusted_user(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.id = 5
        mock_user.role = UserRole.TRUSTED_USER
        mock_user.is_active = True

        mock_item = MagicMock()
        mock_item.id = 100

        session.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_item,
        ]

        mock_fb = MagicMock()
        mock_fb.id = 1
        session.add.return_value = None
        session.commit.return_value = None

        with patch('sigmaprice.feedback.manager.FeedbackItem', return_value=mock_fb):
            result = create_comment(
                user_id=5,
                catalog_item_id=100,
                comment="Wrong price for this item",
                session=session,
            )

        assert result.id == 1
        assert session.add.called

    @patch('sigmaprice.core.database.get_session')
    def test_create_comment_admin(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.role = UserRole.ADMIN
        mock_user.is_active = True

        mock_item = MagicMock()
        mock_item.id = 100

        session.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_item,
        ]

        mock_fb = MagicMock()
        mock_fb.id = 2
        with patch('sigmaprice.feedback.manager.FeedbackItem', return_value=mock_fb):
            result = create_comment(
                user_id=1,
                catalog_item_id=100,
                comment="Category is wrong",
                session=session,
            )

        assert result.id == 2

    @patch('sigmaprice.core.database.get_session')
    def test_create_comment_regular_user_raises(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.role = UserRole.USER
        mock_user.is_active = True

        session.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(ValidationError, match="cannot leave comments"):
            create_comment(
                user_id=10,
                catalog_item_id=100,
                comment="I found an error",
                session=session,
            )

    @patch('sigmaprice.core.database.get_session')
    def test_create_comment_inactive_user_raises(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.id = 5
        mock_user.role = UserRole.TRUSTED_USER
        mock_user.is_active = False

        session.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(ValidationError, match="Inactive"):
            create_comment(
                user_id=5,
                catalog_item_id=100,
                comment="Test",
                session=session,
            )

    @patch('sigmaprice.core.database.get_session')
    def test_create_comment_empty_text(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.TRUSTED_USER
        mock_user.is_active = True

        mock_item = MagicMock()

        session.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_item,
        ]

        with pytest.raises(ValidationError, match="cannot be empty"):
            create_comment(
                user_id=5,
                catalog_item_id=100,
                comment="   ",
                session=session,
            )

    @patch('sigmaprice.core.database.get_session')
    def test_create_comment_item_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.TRUSTED_USER
        mock_user.is_active = True

        session.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            None,
        ]

        with pytest.raises(ValidationError, match="not found"):
            create_comment(
                user_id=5,
                catalog_item_id=999,
                comment="Test comment",
                session=session,
            )

    @patch('sigmaprice.core.database.get_session')
    def test_get_comment_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_fb = MagicMock()
        mock_fb.id = 1
        mock_fb.comment = "test"
        session.query.return_value.filter.return_value.first.return_value = mock_fb

        result = get_comment(1, session=session)
        assert result is not None
        assert result.id == 1

    @patch('sigmaprice.core.database.get_session')
    def test_list_comments_by_status(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_fb = MagicMock()
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_fb]

        result = list_comments(
            filters={"status": FeedbackStatus.PENDING},
            session=session,
        )
        assert len(result) == 1

    @patch('sigmaprice.core.database.get_session')
    def test_get_pending_comments(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_pending_comments(session=session)
        assert result == []


class TestAnalyzer:
    """Test AI comment analysis."""

    @patch('sigmaprice.core.database.get_session')
    def test_analyze_comment_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        result = analyze_comment(999, session=session)
        assert result["found"] is False

    @patch('sigmaprice.core.database.get_session')
    @patch('sigmaprice.feedback.analyzer._research_comment')
    @patch('sigmaprice.feedback.analyzer._keyword_confidence')
    def test_analyze_low_confidence_goes_to_manual(
        self, mock_kw, mock_research, mock_get_session
    ):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_fb = MagicMock()
        mock_fb.id = 1
        mock_fb.catalog_item_id = 100
        mock_fb.comment = "Price seems wrong"
        mock_fb.status = FeedbackStatus.PENDING

        mock_item = MagicMock()
        mock_item.name = "Test Item"
        mock_item.manufacturer = "MSI"

        session.query.return_value.filter.return_value.first.side_effect = [
            mock_fb,
            mock_item,
        ]

        mock_research.return_value = {"found": False, "info": "", "confidence": 0.0}
        mock_kw.return_value = 0.5

        result = analyze_comment(1, session=session)
        assert result["confidence"] == 0.5
        assert result["auto_resolved"] is False


class TestResolver:
    """Test manual and auto resolution."""

    @patch('sigmaprice.core.database.get_session')
    def test_resolve_auto_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        result = resolve_auto(999, session=session)
        assert result is False

    @patch('sigmaprice.core.database.get_session')
    def test_resolve_manual_admin_only(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.role = UserRole.USER

        session.query.return_value.filter.return_value.first.return_value = mock_admin

        with pytest.raises(ValidationError, match="Only admin"):
            resolve_manual(
                comment_id=1,
                admin_id=1,
                resolution="Fixed",
                session=session,
            )

    @patch('sigmaprice.core.database.get_session')
    def test_resolve_manual_success(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.role = UserRole.ADMIN

        mock_fb = MagicMock()
        mock_fb.id = 1
        mock_fb.comment = "test"

        session.query.return_value.filter.return_value.first.side_effect = [
            mock_admin,
            mock_fb,
        ]

        with patch('sigmaprice.feedback.resolver._learn_from_admin'):
            result = resolve_manual(
                comment_id=1,
                admin_id=1,
                resolution="Applied fix",
                session=session,
            )

        assert result is not None
        assert session.commit.called

    @patch('sigmaprice.core.database.get_session')
    def test_reject_comment_success(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_admin = MagicMock()
        mock_admin.id = 1
        mock_admin.role = UserRole.ADMIN

        mock_fb = MagicMock()
        mock_fb.id = 1

        session.query.return_value.filter.return_value.first.side_effect = [
            mock_admin,
            mock_fb,
        ]

        result = reject_comment(
            comment_id=1,
            admin_id=1,
            reason="Not an error",
            session=session,
        )

        assert result is not None
        assert session.commit.called


class TestReports:
    """Test report generation."""

    @patch('sigmaprice.core.database.get_session')
    def test_generate_report_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        result = generate_report(999, session=session)
        assert "error" in result

    @patch('sigmaprice.core.database.get_session')
    def test_generate_report_success(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_fb = MagicMock()
        mock_fb.id = 1
        mock_fb.user_id = 5
        mock_fb.catalog_item_id = 100
        mock_fb.comment = "Test comment"
        mock_fb.ai_resolution = "AI found issue"
        mock_fb.admin_notes = "Admin fixed"
        mock_fb.status = FeedbackStatus.RESOLVED
        mock_fb.auto_fixed = False
        mock_fb.created_at = None
        mock_fb.resolved_at = None

        mock_user = MagicMock()
        mock_user.id = 5
        mock_user.username = "testuser"
        mock_user.display_name = "Test User"

        mock_item = MagicMock()
        mock_item.id = 100
        mock_item.code = "12345678"
        mock_item.name = "Test Item"

        session.query.return_value.filter.return_value.first.side_effect = [
            mock_fb,
            mock_user,
            mock_item,
        ]

        result = generate_report(1, session=session)
        assert result["comment_id"] == 1
        assert result["original_comment"] == "Test comment"
        assert result["user"]["username"] == "testuser"

    @patch('sigmaprice.core.database.get_session')
    def test_generate_summary(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        session.query.return_value.count.return_value = 10
        session.query.return_value.filter.return_value.count.return_value = 2

        result = generate_summary(session=session)
        assert result["total"] == 10
