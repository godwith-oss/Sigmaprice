"""Unique 8-digit code generation for catalog items"""
import random
from sqlalchemy.orm import Session
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 10


def generate_code(session: Session) -> str:
    """
    Generate a unique 8-digit code for a new catalog item.

    Rules:
    - 8 digits
    - Does not start with 0
    - Unique within catalog_items table

    Algorithm:
    1. Random int from 10000000 to 99999999
    2. Check uniqueness in DB
    3. If taken, retry (max 10 attempts)
    4. After 10 failures, raise RuntimeError

    At 100k items: collision probability ~10%. 10 collisions in a row: ~10^-10.
    """
    from sigmaprice.db.models import CatalogItem

    for attempt in range(1, MAX_RETRIES + 1):
        code = str(random.randint(10000000, 99999999))

        exists = session.query(CatalogItem).filter(
            CatalogItem.code == code
        ).first()

        if not exists:
            logger.debug(f"Generated code: {code} (attempt {attempt})")
            return code

        logger.warning(f"Code collision: {code} (attempt {attempt})")

    raise RuntimeError(
        f"Failed to generate unique code after {MAX_RETRIES} attempts. "
        f"Table may be too full (>{90_000_000} items)"
    )
