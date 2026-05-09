"""Supplier CRUD operations"""
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sigmaprice.db.models import Supplier, SupplierRule, SupplierColumnMap
from sigmaprice.core.exceptions import SupplierError, ValidationError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def create_supplier(
    name: str,
    country: str,
    currency: str,
    vat_included: bool,
    price_formula: Optional[str] = None,
    session: Optional[Session] = None
) -> Supplier:
    """
    Create a new supplier.

    Args:
        name: Supplier name
        country: Country name
        currency: Currency code ('RUB', 'USD', 'EUR')
        vat_included: Whether VAT is included in price
        price_formula: Price calculation formula
        session: Database session (optional, will create if not provided)

    Returns:
        Created Supplier object

    Raises:
        ValidationError: If validation fails

    Examples of price_formula:
        - 'price' (no changes)
        - 'price * 1.2' (20% markup)
        - 'price * usd_rate' (convert by rate)
        - 'price * usd_rate * 1.2' (convert + VAT)
    """
    if not name or len(name.strip()) == 0:
        raise ValidationError("Supplier name cannot be empty")

    if currency not in ['RUB', 'USD', 'EUR']:
        raise ValidationError(f"Invalid currency: {currency}. Must be RUB, USD, or EUR")

    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    try:
        supplier = Supplier(
            name=name.strip(),
            country=country.strip(),
            currency=currency.upper(),
            vat_included=vat_included,
            price_formula=price_formula
        )
        session.add(supplier)
        session.commit()
        session.refresh(supplier)

        logger.info(f"Created supplier: {supplier.name} (ID: {supplier.id})")
        return supplier

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create supplier: {e}")
        raise SupplierError(f"Failed to create supplier: {e}")


def get_supplier(supplier_id: int, session: Optional[Session] = None) -> Optional[Supplier]:
    """
    Get supplier by ID.

    Args:
        supplier_id: Supplier ID
        session: Database session

    Returns:
        Supplier object or None if not found
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(Supplier).filter(Supplier.id == supplier_id).first()


def get_supplier_by_name(name: str, session: Optional[Session] = None) -> Optional[Supplier]:
    """Get supplier by name (case-insensitive)."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(Supplier).filter(
        Supplier.name.ilike(name)
    ).first()


def update_supplier(
    supplier_id: int,
    session: Optional[Session] = None,
    **kwargs
) -> Supplier:
    """
    Update supplier fields.

    Args:
        supplier_id: Supplier ID
        session: Database session
        **kwargs: Fields to update (name, country, currency, vat_included, price_formula)

    Returns:
        Updated Supplier object

    Raises:
        SupplierError: If supplier not found
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise SupplierError(f"Supplier with ID {supplier_id} not found")

    allowed_fields = ['name', 'country', 'currency', 'vat_included', 'price_formula']

    for key, value in kwargs.items():
        if key in allowed_fields and value is not None:
            if key == 'name' and len(value.strip()) == 0:
                raise ValidationError("Supplier name cannot be empty")
            if key == 'currency' and value not in ['RUB', 'USD', 'EUR']:
                raise ValidationError(f"Invalid currency: {value}")
            setattr(supplier, key, value.strip() if isinstance(value, str) else value)

    session.commit()
    session.refresh(supplier)

    logger.info(f"Updated supplier: {supplier.name} (ID: {supplier.id})")
    return supplier


def delete_supplier(supplier_id: int, session: Optional[Session] = None) -> bool:
    """
    Delete supplier and all related data.

    Args:
        supplier_id: Supplier ID
        session: Database session

    Returns:
        True if deleted successfully
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        return False

    supplier_name = supplier.name
    session.delete(supplier)
    session.commit()

    logger.info(f"Deleted supplier: {supplier_name} (ID: {supplier_id})")
    return True


def list_suppliers(session: Optional[Session] = None) -> list[Supplier]:
    """Get list of all suppliers."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(Supplier).order_by(Supplier.name).all()