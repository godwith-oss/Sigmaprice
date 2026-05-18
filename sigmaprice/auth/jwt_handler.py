"""JWT token handling — access + refresh tokens"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError, ExpiredSignatureError
from sigmaprice.core.config import get_secret_key
from sigmaprice.auth.models import TokenPair

ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)
ALGORITHM = "HS256"


def create_tokens(user_id: int, role: str) -> TokenPair:
    """
    Create access + refresh token pair.

    Access token payload:
        sub: user_id, role: role, type: "access", iat, exp (+15 min)

    Refresh token payload:
        sub: user_id, type: "refresh", jti: unique_id, iat, exp (+7 days)
    """
    now = datetime.now(timezone.utc)
    secret = get_secret_key()

    access_payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE,
    }
    access_token = jwt.encode(access_payload, secret, algorithm=ALGORITHM)

    refresh_payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": _generate_jti(),
        "iat": now,
        "exp": now + REFRESH_TOKEN_EXPIRE,
    }
    refresh_token = jwt.encode(refresh_payload, secret, algorithm=ALGORITHM)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(ACCESS_TOKEN_EXPIRE.total_seconds()),
    )


def verify_access_token(token: str) -> dict:
    """
    Verify and decode an access token.

    Returns:
        Payload dict with keys: sub, role, type

    Raises:
        ExpiredSignatureError: Token expired
        JWTError: Invalid token
    """
    secret = get_secret_key()
    payload = jwt.decode(token, secret, algorithms=[ALGORITHM])

    if payload.get("type") != "access":
        raise JWTError("Token is not an access token")

    return payload


def verify_refresh_token(token: str) -> dict:
    """
    Verify and decode a refresh token.

    Returns:
        Payload dict with keys: sub, type, jti, exp

    Raises:
        ExpiredSignatureError: Token expired
        JWTError: Invalid token
    """
    secret = get_secret_key()
    payload = jwt.decode(token, secret, algorithms=[ALGORITHM])

    if payload.get("type") != "refresh":
        raise JWTError("Token is not a refresh token")

    return payload


def decode_token_unsafe(token: str) -> Optional[dict]:
    """Decode token without verifying expiration (for blacklist checks)."""
    try:
        return jwt.decode(
            token, get_secret_key(),
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
    except JWTError:
        return None


def _generate_jti() -> str:
    import uuid
    return str(uuid.uuid4())
