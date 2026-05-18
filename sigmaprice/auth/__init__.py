"""Auth module — users, permissions, JWT authentication"""
from sigmaprice.auth.users import (
    create_user,
    authenticate,
    get_user,
    get_user_by_username,
    update_user,
    delete_user,
    list_users,
)
from sigmaprice.auth.permissions import (
    grant_permission,
    revoke_permission,
    get_user_permissions,
    check_category_access,
    check_supplier_access,
    get_allowed_categories,
    get_allowed_suppliers,
)
from sigmaprice.auth.jwt_handler import (
    create_tokens,
    verify_access_token,
    verify_refresh_token,
    decode_token_unsafe,
)
from sigmaprice.auth.blacklist import (
    revoke_token,
    is_token_revoked,
)
from sigmaprice.auth.password import (
    hash_password,
    verify_password,
)

__all__ = [
    "create_user",
    "authenticate",
    "get_user",
    "get_user_by_username",
    "update_user",
    "delete_user",
    "list_users",
    "grant_permission",
    "revoke_permission",
    "get_user_permissions",
    "check_category_access",
    "check_supplier_access",
    "get_allowed_categories",
    "get_allowed_suppliers",
    "create_tokens",
    "verify_access_token",
    "verify_refresh_token",
    "decode_token_unsafe",
    "revoke_token",
    "is_token_revoked",
    "hash_password",
    "verify_password",
]
