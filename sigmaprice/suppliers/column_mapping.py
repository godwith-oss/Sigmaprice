"""Column mapping for supplier price files"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sigmaprice.db.models import Supplier, SupplierColumnMap
from sigmaprice.core.exceptions import SupplierError, ValidationError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


ALLOWED_FIELDS = [
    'code', 'name', 'description', 'price', 'availability',
    'quantity', 'warranty_months', 'article', 'ean', 'manufacturer',
    'delivery_type', 'category'
]


def set_column_mapping(
    supplier_id: int,
    mapping: Dict[str, str],
    session: Optional[Session] = None
) -> bool:
    """
    Save column mapping for supplier's price file.

    Args:
        supplier_id: Supplier ID
        mapping: Dict of our_field -> supplier_column
            Example:
            {
                'code': 'Код',
                'name': 'Наименование',
                'price': 'Цена',
                'availability': 'Наличие',
                'article': 'Артикул',
                'ean': 'Штрих-код'
            }
        session: Database session

    Returns:
        True if saved successfully

    Raises:
        SupplierError: If supplier not found
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise SupplierError(f"Supplier with ID {supplier_id} not found")

    for field in mapping.keys():
        if field not in ALLOWED_FIELDS:
            raise ValidationError(f"Invalid field name: {field}. Allowed: {ALLOWED_FIELDS}")

    session.query(SupplierColumnMap).filter(
        SupplierColumnMap.supplier_id == supplier_id
    ).delete()

    for our_field, supplier_column in mapping.items():
        mapping_obj = SupplierColumnMap(
            supplier_id=supplier_id,
            our_field=our_field,
            supplier_column=supplier_column.strip()
        )
        session.add(mapping_obj)

    session.commit()
    logger.info(f"Set column mapping for supplier {supplier_id}")
    return True


def get_column_mapping(
    supplier_id: int,
    session: Optional[Session] = None
) -> Dict[str, str]:
    """
    Get saved column mapping for supplier.

    Args:
        supplier_id: Supplier ID
        session: Database session

    Returns:
        Dict of our_field -> supplier_column
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    mappings = session.query(SupplierColumnMap).filter(
        SupplierColumnMap.supplier_id == supplier_id
    ).all()

    result = {}
    for m in mappings:
        result[m.our_field] = m.supplier_column

    return result


def clear_column_mapping(
    supplier_id: int,
    session: Optional[Session] = None
) -> bool:
    """Clear all column mappings for a supplier."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    deleted = session.query(SupplierColumnMap).filter(
        SupplierColumnMap.supplier_id == supplier_id
    ).delete()

    session.commit()
    logger.info(f"Cleared {deleted} column mappings for supplier {supplier_id}")
    return deleted > 0


def get_field_by_column(
    supplier_id: int,
    supplier_column: str,
    session: Optional[Session] = None
) -> Optional[str]:
    """
    Get our field name by supplier's column name.

    Useful for parsing price files where you know the column header
    and need to find which field it maps to.

    Args:
        supplier_id: Supplier ID
        supplier_column: Column header from price file
        session: Database session

    Returns:
        Our field name or None if not found
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    mapping = session.query(SupplierColumnMap).filter(
        SupplierColumnMap.supplier_id == supplier_id,
        SupplierColumnMap.supplier_column == supplier_column.strip()
    ).first()

    return mapping.our_field if mapping else None