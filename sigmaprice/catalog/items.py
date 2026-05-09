"""Catalog items management - stub for Module 5"""
from typing import Optional
from decimal import Decimal
from sigmaprice.core.database import create_session
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def generate_item_code() -> str:
    """Generate unique 8-digit code for new catalog item."""
    import random
    code = random.randint(10000000, 99999999)
    return str(code)


def get_item_by_code(code: str, session=None) -> Optional['CatalogItem']:
    """Get catalog item by code."""
    from sigmaprice.db.models import CatalogItem

    if session is None:
        session = create_session()

    return session.query(CatalogItem).filter(CatalogItem.code == code).first()


def get_item_by_id(item_id: int, session=None) -> Optional['CatalogItem']:
    """Get catalog item by ID."""
    from sigmaprice.db.models import CatalogItem

    if session is None:
        session = create_session()

    return session.query(CatalogItem).filter(CatalogItem.id == item_id).first()


def create_catalog_item(
    name: str,
    description: Optional[str] = None,
    manufacturer: Optional[str] = None,
    article: Optional[str] = None,
    ean: Optional[str] = None,
    delivery_type: Optional[str] = None,
    session=None
) -> 'CatalogItem':
    """Create new catalog item."""
    from sigmaprice.db.models import CatalogItem

    if session is None:
        session = create_session()

    code = generate_item_code()

    while get_item_by_code(code, session):
        code = generate_item_code()

    item = CatalogItem(
        code=code,
        name=name,
        description=description,
        manufacturer=manufacturer,
        article=article,
        ean=ean
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    logger.info(f"Created catalog item: {code} - {name}")
    return item