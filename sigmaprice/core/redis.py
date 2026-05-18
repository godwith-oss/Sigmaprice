"""Redis connection helper"""
import redis as redis_lib
from sigmaprice.core.config import get_redis_url

_redis_client = None


def get_redis():
    """Get or create Redis client (lazy init)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis_lib.from_url(
            get_redis_url(),
            decode_responses=True,
        )
    return _redis_client
