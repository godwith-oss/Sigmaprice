"""User CRUD operations"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sigmaprice.db.models import User, UserRole
from sigmaprice.auth.password import hash_password, verify_password
from sigmaprice.auth.models import UserCreate, UserUpdate, UserResponse, UserRoleEnum
from sigmaprice.core.exceptions import ValidationError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def create_user(
    username: str,
    password: str,
    role: str = "user",
    display_name: Optional[str] = None,
    created_by: Optional[int] = None,
    session: Optional[Session] = None,
) -> User:
    """
    Create a new user.

    Args:
        username: Unique login (stored in lowercase)
        password: Plain-text password (will be hashed)
        role: One of 'admin', 'trusted_user', 'user'
        display_name: Display name (original case)
        created_by: ID of admin who created this user

    Returns:
        Created User object

    Raises:
        ValidationError: If username exists or role is invalid
        PermissionError: If created_by is not admin
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    username_lower = username.strip().lower()

    if role not in ["admin", "trusted_user", "user"]:
        raise ValidationError(
            f"Invalid role: {role}. Must be admin, trusted_user, or user"
        )

    existing = session.query(User).filter(
        User.username == username_lower
    ).first()
    if existing:
        raise ValidationError(f"Username '{username}' already exists")

    hashed = hash_password(password)

    user = User(
        username=username_lower,
        password_hash=hashed,
        role=UserRole(role),
        display_name=display_name or username.strip(),
        is_trusted=(role == "trusted_user"),
        created_by=created_by,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info(f"Created user: {user.username} (role: {user.role.value}, ID: {user.id})")
    return user


def authenticate(
    username: str,
    password: str,
    session: Optional[Session] = None,
) -> Optional[User]:
    """
    Authenticate user by username and password.

    Args:
        username: Login (case-insensitive)
        password: Plain-text password

    Returns:
        User object if authenticated, None if invalid

    Side effects:
        Updates last_login on successful authentication
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    user = session.query(User).filter(
        User.username == username.strip().lower()
    ).first()

    if not user:
        return None

    if not user.is_active:
        logger.warning(f"Inactive user '{username}' attempted login")
        return None

    if not verify_password(password, user.password_hash):
        return None

    user.last_login = datetime.now(timezone.utc)
    session.commit()

    logger.info(f"User authenticated: {user.username}")
    return user


def get_user(
    user_id: int,
    session: Optional[Session] = None,
) -> Optional[User]:
    """Get user by ID."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(User).filter(User.id == user_id).first()


def get_user_by_username(
    username: str,
    session: Optional[Session] = None,
) -> Optional[User]:
    """Get user by username (case-insensitive)."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(User).filter(
        User.username == username.strip().lower()
    ).first()


def update_user(
    user_id: int,
    session: Optional[Session] = None,
    **kwargs,
) -> User:
    """
    Update user fields.

    Allowed fields:
        username, password, role, display_name, is_active

    Raises:
        ValidationError: If user not found or username taken
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValidationError(f"User with ID {user_id} not found")

    if "username" in kwargs:
        new_username = kwargs["username"].strip().lower()
        existing = session.query(User).filter(
            User.username == new_username,
            User.id != user_id,
        ).first()
        if existing:
            raise ValidationError(f"Username '{kwargs['username']}' already taken")
        user.username = new_username

    if "password" in kwargs:
        user.password_hash = hash_password(kwargs["password"])

    if "role" in kwargs:
        role = kwargs["role"]
        if role not in ["admin", "trusted_user", "user"]:
            raise ValidationError(f"Invalid role: {role}")
        user.role = UserRole(role)
        user.is_trusted = (role == "trusted_user")

    if "display_name" in kwargs:
        user.display_name = kwargs["display_name"]

    if "is_active" in kwargs:
        user.is_active = kwargs["is_active"]

    session.commit()
    session.refresh(user)

    logger.info(f"Updated user: {user.username} (ID: {user.id})")
    return user


def delete_user(
    user_id: int,
    session: Optional[Session] = None,
) -> bool:
    """
    Delete user and all their permissions.
    Feedback comments remain with 'deleted user' note.

    Returns True if deleted, False if not found.
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    username = user.username
    session.delete(user)
    session.commit()

    logger.info(f"Deleted user: {username} (ID: {user_id})")
    return True


def list_users(
    session: Optional[Session] = None,
) -> List[User]:
    """List all users."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(User).order_by(User.username).all()
