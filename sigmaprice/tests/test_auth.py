"""Tests for Module 8 - Auth (Users, Permissions, JWT, Passwords)"""
import pytest
from unittest.mock import MagicMock, patch
from sigmaprice.auth import (
    create_user,
    authenticate,
    get_user,
    get_user_by_username,
    update_user,
    delete_user,
    list_users,
    grant_permission,
    revoke_permission,
    check_category_access,
    check_supplier_access,
    get_allowed_categories,
    get_allowed_suppliers,
    create_tokens,
    verify_access_token,
    verify_refresh_token,
    revoke_token,
    is_token_revoked,
    hash_password,
    verify_password,
)
from sigmaprice.core.exceptions import ValidationError
from sigmaprice.db.models import UserRole


class TestPassword:
    """Test password hashing and verification."""

    def test_hash_password_creates_hash(self):
        hashed = hash_password("securePass123")
        assert hashed != "securePass123"
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        hashed = hash_password("securePass123")
        assert verify_password("securePass123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("securePass123")
        assert verify_password("wrongPass123", hashed) is False

    def test_hash_short_password_raises(self):
        with pytest.raises(ValidationError, match="8 characters"):
            hash_password("short")

    def test_different_salts_produce_different_hashes(self):
        h1 = hash_password("samePassword123")
        h2 = hash_password("samePassword123")
        assert h1 != h2


class TestUserCRUD:
    """Test user creation, authentication, CRUD."""

    @patch('sigmaprice.core.database.get_session')
    @patch('sigmaprice.auth.users.hash_password')
    def test_create_user_success(self, mock_hash, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        mock_hash.return_value = "$2b$12$...hashed..."

        session.query.return_value.filter.return_value.first.return_value = None

        user = MagicMock()
        user.id = 1
        user.username = "ivanpetrov"
        user.role = UserRole.USER
        session.add.return_value = None
        session.commit.return_value = None

        with patch('sigmaprice.auth.users.User', return_value=user):
            result = create_user(
                username="IvanPetrov",
                password="securePass123",
                role="user",
                session=session,
            )

        assert result.username == "ivanpetrov"
        assert session.add.called

    @patch('sigmaprice.core.database.get_session')
    def test_create_user_duplicate_username(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        existing = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = existing

        with pytest.raises(ValidationError, match="already exists"):
            create_user(
                username="existinguser",
                password="securePass123",
                session=session,
            )

    @patch('sigmaprice.core.database.get_session')
    def test_create_user_invalid_role(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValidationError, match="Invalid role"):
            create_user(
                username="testuser",
                password="securePass123",
                role="superadmin",
                session=session,
            )

    @patch('sigmaprice.core.database.get_session')
    def test_authenticate_success(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "ivanpetrov"
        mock_user.password_hash = "$2b$12$...hashed..."
        mock_user.is_active = True

        session.query.return_value.filter.return_value.first.return_value = mock_user

        with patch('sigmaprice.auth.users.verify_password', return_value=True):
            result = authenticate("IvanPetrov", "securePass123", session=session)

        assert result is not None
        assert result.username == "ivanpetrov"
        assert mock_user.last_login is not None

    @patch('sigmaprice.core.database.get_session')
    def test_authenticate_wrong_password(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.is_active = True
        session.query.return_value.filter.return_value.first.return_value = mock_user

        with patch('sigmaprice.auth.users.verify_password', return_value=False):
            result = authenticate("test", "wrong", session=session)

        assert result is None

    @patch('sigmaprice.core.database.get_session')
    def test_authenticate_inactive_user(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.is_active = False
        session.query.return_value.filter.return_value.first.return_value = mock_user

        result = authenticate("test", "pass", session=session)
        assert result is None

    @patch('sigmaprice.core.database.get_session')
    def test_get_user_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.id = 1
        session.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_user(1, session=session)
        assert result is not None

    @patch('sigmaprice.core.database.get_session')
    def test_update_user_success(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "olduser"
        session.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            None,
        ]

        result = update_user(
            1,
            username="newuser",
            display_name="New User",
            session=session,
        )

        assert mock_user.username == "newuser"
        assert session.commit.called

    @patch('sigmaprice.core.database.get_session')
    def test_delete_user_success(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "todelete"
        session.query.return_value.filter.return_value.first.return_value = mock_user

        result = delete_user(1, session=session)
        assert result is True
        assert session.delete.called


class TestPermissions:
    """Test permission management."""

    @patch('sigmaprice.core.database.get_session')
    def test_grant_permission_category(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.id = 5
        mock_user.role = UserRole.USER
        session.query.return_value.filter.return_value.first.return_value = mock_user

        session.add.return_value = None
        session.commit.return_value = None

        perm = MagicMock()
        perm.id = 1

        with patch('sigmaprice.auth.permissions.UserPermission', return_value=perm):
            result = grant_permission(
                user_id=5,
                category_id=2,
                supplier_id=None,
                session=session,
            )

        assert session.add.called

    @patch('sigmaprice.core.database.get_session')
    def test_grant_permission_user_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValidationError, match="not found"):
            grant_permission(user_id=999, category_id=2, session=session)

    @patch('sigmaprice.core.database.get_session')
    def test_check_category_access_admin(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.ADMIN
        session.query.return_value.filter.return_value.first.return_value = mock_user

        result = check_category_access(user_id=1, category_id=5, session=session)
        assert result is True

    @patch('sigmaprice.core.database.get_session')
    def test_check_category_access_regular_user_with_permission(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.USER
        session.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            MagicMock(),
        ]

        result = check_category_access(user_id=5, category_id=2, session=session)
        assert result is True

    @patch('sigmaprice.core.database.get_session')
    def test_check_supplier_access_regular_user_no_permission(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.USER
        session.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            None,
        ]

        result = check_supplier_access(user_id=5, supplier_id=3, session=session)
        assert result is False

    @patch('sigmaprice.core.database.get_session')
    def test_get_allowed_categories_admin_returns_none(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.ADMIN
        mock_user.is_active = True
        session.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_allowed_categories(user_id=1, session=session)
        assert result is None

    @patch('sigmaprice.core.database.get_session')
    def test_get_allowed_categories_wildcard_returns_none(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.USER
        mock_user.is_active = True
        session.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            MagicMock(),
        ]

        result = get_allowed_categories(user_id=5, session=session)
        assert result is None

    @patch('sigmaprice.core.database.get_session')
    def test_get_allowed_categories_specific_list(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.USER
        mock_user.is_active = True
        session.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            None,
        ]
        session.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            (2,), (5,)
        ]

        result = get_allowed_categories(user_id=5, session=session)
        assert result == [2, 5]

    @patch('sigmaprice.core.database.get_session')
    def test_get_allowed_suppliers_admin(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.ADMIN
        mock_user.is_active = True
        session.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_allowed_suppliers(user_id=1, session=session)
        assert result is None

    @patch('sigmaprice.core.database.get_session')
    def test_inactive_user_no_categories(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.role = UserRole.USER
        mock_user.is_active = False
        session.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_allowed_categories(user_id=5, session=session)
        assert result == []


class TestJWT:
    """Test JWT token creation and verification."""

    def test_create_tokens_returns_pair(self):
        tokens = create_tokens(user_id=1, role="user")
        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == 900

    def test_verify_access_token_success(self):
        tokens = create_tokens(user_id=1, role="admin")
        payload = verify_access_token(tokens.access_token)
        assert payload["sub"] == "1"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_verify_refresh_token_success(self):
        tokens = create_tokens(user_id=1, role="user")
        payload = verify_refresh_token(tokens.refresh_token)
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_access_token_rejects_refresh_token(self):
        tokens = create_tokens(user_id=1, role="user")
        from jose.exceptions import JWTError
        with pytest.raises(JWTError):
            verify_access_token(tokens.refresh_token)

    def test_refresh_token_rejects_access_token(self):
        tokens = create_tokens(user_id=1, role="user")
        from jose.exceptions import JWTError
        with pytest.raises(JWTError):
            verify_refresh_token(tokens.access_token)


class TestBlacklist:
    """Test token revocation."""

    def test_revoke_token_no_redis(self):
        tokens = create_tokens(user_id=1, role="user")
        with patch('sigmaprice.auth.blacklist._get_redis', return_value=None):
            result = revoke_token(tokens.refresh_token)
            assert result is False

    def test_is_token_revoked_no_redis(self):
        tokens = create_tokens(user_id=1, role="user")
        with patch('sigmaprice.auth.blacklist._get_redis', return_value=None):
            result = is_token_revoked(tokens.refresh_token)
            assert result is False
