"""Redis token blacklist for refresh token revocation"""
from typing import Optional
from sigmaprice.auth.jwt_handler import decode_token_unsafe
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def _get_redis():
    """Lazy-load Redis connection."""
    try:
        from sigmaprice.core.redis import get_redis
        return get_redis()
    except Exception:
        return None


def revoke_token(token: str) -> bool:
    """
    Add a token to the blacklist.

    Args:
        token: JWT token (access or refresh)

    Returns:
        True if successfully added to blacklist
    """
    redis = _get_redis()
    if redis is None:
        logger.warning("Redis not available, token revocation skipped")
        return False

    payload = decode_token_unsafe(token)
    if payload is None:
        return False

    jti = payload.get("jti")
    if jti is None:
        return False

    exp = payload.get("exp")
    now = int(__import__("time").time())
    ttl = max(exp - now, 1) if exp else 86400

    redis.setex(f"blacklist:{jti}", int(ttl), "revoked")
    logger.debug(f"Token {jti} revoked (TTL: {ttl}s)")
    return True


def is_token_revoked(token: str) -> bool:
    """
    Check if a token is in the blacklist.

    Args:
        token: JWT token

    Returns:
        True if token is revoked
    """
    redis = _get_redis()
    if redis is None:
        return False

    payload = decode_token_unsafe(token)
    if payload is None:
        return False

    jti = payload.get("jti")
    if jti is None:
        return False

    return redis.exists(f"blacklist:{jti}") > 0
