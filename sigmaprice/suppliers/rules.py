"""Supplier exclusion rules handling"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sigmaprice.db.models import SupplierRule, Supplier, RuleType
from sigmaprice.core.types import RawItem
from sigmaprice.core.exceptions import SupplierError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def add_rule(
    supplier_id: int,
    rule_type: str,
    rule_value: str,
    session: Optional[Session] = None
) -> SupplierRule:
    """
    Add an exclusion rule to a supplier.

    Args:
        supplier_id: Supplier ID
        rule_type: Type of rule:
            - 'exclude_sheet' - Exclude Excel sheet by name
            - 'exclude_category' - Exclude category
            - 'exclude_keyword' - Exclude by keyword in name
            - 'price_range' - Price range filter (min:100,max:50000)
        rule_value: Rule value (e.g., 'Б/У', 'Расходники', 'demo')
        session: Database session

    Returns:
        Created SupplierRule object

    Raises:
        SupplierError: If supplier not found or invalid rule type
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise SupplierError(f"Supplier with ID {supplier_id} not found")

    try:
        rule_type_enum = RuleType(rule_type)
    except ValueError:
        raise SupplierError(f"Invalid rule type: {rule_type}")

    if not rule_value or len(rule_value.strip()) == 0:
        raise SupplierError("Rule value cannot be empty")

    rule = SupplierRule(
        supplier_id=supplier_id,
        rule_type=rule_type_enum,
        rule_value=rule_value.strip()
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)

    logger.info(f"Added rule {rule_type}={rule_value} for supplier {supplier_id}")
    return rule


def get_rules(supplier_id: int, session: Optional[Session] = None) -> List[SupplierRule]:
    """
    Get all rules for a supplier.

    Args:
        supplier_id: Supplier ID
        session: Database session

    Returns:
        List of SupplierRule objects
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(SupplierRule).filter(
        SupplierRule.supplier_id == supplier_id
    ).all()


def delete_rule(rule_id: int, session: Optional[Session] = None) -> bool:
    """Delete a specific rule."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    rule = session.query(SupplierRule).filter(SupplierRule.id == rule_id).first()
    if not rule:
        return False

    session.delete(rule)
    session.commit()
    logger.info(f"Deleted rule ID: {rule_id}")
    return True


def should_exclude(supplier_id: int, item: RawItem) -> bool:
    """
    Check if item should be excluded based on supplier rules.

    Args:
        supplier_id: Supplier ID
        item: RawItem from price file

    Returns:
        True if item should be excluded
    """
    from sigmaprice.core.database import get_session
    session = get_session()

    rules = get_rules(supplier_id, session)

    for rule in rules:
        if _apply_rule(rule, item):
            logger.debug(f"Item {item.name} excluded by rule {rule.rule_type.value}:{rule.rule_value}")
            return True

    return False


def _apply_rule(rule: SupplierRule, item: RawItem) -> bool:
    """Apply a single rule to an item."""
    rule_type = rule.rule_type.value
    rule_value = rule.rule_value.lower()

    if rule_type == 'exclude_sheet':
        return False

    elif rule_type == 'exclude_category':
        if item.description and rule_value in item.description.lower():
            return True

    elif rule_type == 'exclude_keyword':
        if rule_value in item.name.lower():
            return True

    elif rule_type == 'price_range':
        try:
            min_price, max_price = _parse_price_range(rule_value)
            return not (min_price <= float(item.price) <= max_price)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid price range format: {rule_value}")
            return False

    return False


def _parse_price_range(range_str: str) -> tuple[float, float]:
    """Parse price range string like 'min:100,max:50000'."""
    parts = range_str.split(',')
    min_price = 0
    max_price = float('inf')

    for part in parts:
        part = part.strip()
        if part.startswith('min:'):
            min_price = float(part[4:])
        elif part.startswith('max:'):
            max_price = float(part[4:])

    return min_price, max_price