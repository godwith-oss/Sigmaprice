"""Category and supplier access permissions"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sigmaprice.db.models import User, UserPermission, UserRole
from sigmaprice.core.exceptions import ValidationError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def grant_permission(
    user_id: int,
    category_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    session: Optional[Session] = None,
) -> UserPermission:
    """
    Grant access to a category and/or supplier.

    NULL = all (AND logic):
    - (category_id=2, supplier_id=None)  -> category 2, any supplier
    - (category_id=None, supplier_id=3)  -> any category, supplier 3
    - (category_id=None, supplier_id=None) -> all categories, all suppliers

    Args:
        user_id: User ID
        category_id: Category ID or None (all categories)
        supplier_id: Supplier ID or None (all suppliers)

    Returns:
        Created Permission object
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValidationError(f"User with ID {user_id} not found")

    if user.role == UserRole.ADMIN:
        logger.warning(
            f"Admin (user_id={user_id}) has full access by role, "
            "permission grant is redundant"
        )

    permission = UserPermission(
        user_id=user_id,
        category_id=category_id,
        supplier_id=supplier_id,
    )
    session.add(permission)
    session.commit()
    session.refresh(permission)

    logger.info(
        f"Granted permission: user={user_id}, category={category_id}, supplier={supplier_id}"
    )
    return permission


def revoke_permission(
    permission_id: int,
    session: Optional[Session] = None,
) -> bool:
    """
    Revoke a permission.

    Returns True if revoked, False if not found.
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    permission = session.query(UserPermission).filter(
        UserPermission.id == permission_id
    ).first()
    if not permission:
        return False

    session.delete(permission)
    session.commit()
    logger.info(f"Revoked permission ID: {permission_id}")
    return True


def get_user_permissions(
    user_id: int,
    session: Optional[Session] = None,
) -> List[UserPermission]:
    """Get all permissions for a user."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(UserPermission).filter(
        UserPermission.user_id == user_id
    ).all()


def check_category_access(
    user_id: int,
    category_id: int,
    session: Optional[Session] = None,
) -> bool:
    """
    Check if user has access to a category.

    Logic:
    1. If role == 'admin' → True
    2. Check user_permissions for match:
       WHERE user_id = X AND (category_id = Y OR category_id IS NULL)

    Returns True if access is granted.
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    if user.role == UserRole.ADMIN:
        return True

    has_access = session.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        (
            (UserPermission.category_id == category_id) |
            (UserPermission.category_id.is_(None))
        )
    ).first()

    return has_access is not None


def check_supplier_access(
    user_id: int,
    supplier_id: int,
    session: Optional[Session] = None,
) -> bool:
    """
    Check if user has access to a supplier.

    Logic:
    1. If role == 'admin' → True
    2. Check user_permissions: WHERE user_id = X AND (supplier_id = Y OR supplier_id IS NULL)
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    if user.role == UserRole.ADMIN:
        return True

    has_access = session.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        (
            (UserPermission.supplier_id == supplier_id) |
            (UserPermission.supplier_id.is_(None))
        )
    ).first()

    return has_access is not None


def get_allowed_categories(
    user_id: int,
    session: Optional[Session] = None,
) -> Optional[List[int]]:
    """
    Get list of allowed category IDs for a user.

    Returns:
        - List of category IDs the user has access to
        - None if user has access to ALL categories (admin or wildcard)
        - Empty list [] if no access
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    user = session.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return []

    if user.role == UserRole.ADMIN:
        return None

    has_all = session.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.category_id.is_(None)
    ).first()

    if has_all:
        return None

    categories = session.query(UserPermission.category_id).filter(
        UserPermission.user_id == user_id,
        UserPermission.category_id.isnot(None)
    ).distinct().all()

    return [c[0] for c in categories]


def get_allowed_suppliers(
    user_id: int,
    session: Optional[Session] = None,
) -> Optional[List[int]]:
    """
    Get list of allowed supplier IDs for a user.

    Returns:
        - List of supplier IDs
        - None if access to ALL suppliers
        - Empty list [] if no access
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    user = session.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return []

    if user.role == UserRole.ADMIN:
        return None

    has_all = session.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.supplier_id.is_(None)
    ).first()

    if has_all:
        return None

    suppliers = session.query(UserPermission.supplier_id).filter(
        UserPermission.user_id == user_id,
        UserPermission.supplier_id.isnot(None)
    ).distinct().all()

    return [s[0] for s in suppliers]
