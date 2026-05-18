"""Password hashing with passlib (bcrypt, rounds=12)"""
from passlib.context import CryptContext
from sigmaprice.core.exceptions import ValidationError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with 12 rounds.

    Args:
        password: Plain-text password (min 8 characters)

    Returns:
        Hashed password string

    Raises:
        ValidationError: If password is too short
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters")
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain-text password
        hashed: Hashed password from database

    Returns:
        True if password matches
    """
    return pwd_context.verify(password, hashed)
