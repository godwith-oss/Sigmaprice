"""Price calculation based on supplier formula"""
from decimal import Decimal
from typing import Optional, Dict
import re
from sqlalchemy.orm import Session
from sigmaprice.db.models import Supplier
from sigmaprice.core.exceptions import SupplierError, ValidationError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)

SAFE_VAR_PATTERN = re.compile(r'^[a-z_][a-z0-9_]*$')


def calculate_price(
    supplier_id: int,
    price_original: Decimal,
    exchange_rates: Optional[Dict[str, float]] = None,
    session: Optional[Session] = None
) -> Decimal:
    """
    Calculate price using supplier's formula.

    Args:
        supplier_id: Supplier ID
        price_original: Original price from supplier
        exchange_rates: Exchange rates dict (e.g., {'usd_rate': 95.5, 'eur_rate': 105.2})
        session: Database session

    Returns:
        Calculated price

    Raises:
        SupplierError: If supplier not found or formula is invalid
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise SupplierError(f"Supplier with ID {supplier_id} not found")

    if not supplier.price_formula:
        return price_original

    formula = supplier.price_formula.strip()
    if not formula or formula == 'price':
        return price_original

    if exchange_rates is None:
        exchange_rates = {}

    try:
        result = _eval_formula(formula, float(price_original), exchange_rates)
        return Decimal(str(round(result, 2)))
    except Exception as e:
        logger.error(f"Failed to calculate price with formula '{formula}': {e}")
        raise ValidationError(f"Invalid price formula: {e}")


def _eval_formula(formula: str, price: float, vars: Dict[str, float]) -> float:
    """
    Safely evaluate a price formula.

    Only allows: price, numbers, basic operators, and predefined variables.
    """
    allowed_names = {
        'price': price,
        'usd_rate': vars.get('usd_rate', 1.0),
        'eur_rate': vars.get('eur_rate', 1.0),
        'rub_rate': vars.get('rub_rate', 1.0),
        'vat': 1.2,
        'nds': 1.2,
    }

    allowed_names.update(vars)

    for name in vars.keys():
        if SAFE_VAR_PATTERN.match(name):
            allowed_names[name] = vars[name]

    try:
        result = eval(formula, {"__builtins__": {}}, allowed_names)
        return float(result)
    except (NameError, SyntaxError, TypeError) as e:
        raise ValidationError(f"Formula evaluation error: {e}")


def validate_formula(formula: str) -> bool:
    """
    Validate a price formula.

    Returns True if formula is safe to use.
    """
    if not formula or formula.strip() == 'price':
        return True

    formula = formula.strip()

    if not SAFE_VAR_PATTERN.match(formula):
        return False

    forbidden = ['import', 'os', 'sys', 'subprocess', 'eval', 'exec', 'open', 'file']
    for word in forbidden:
        if word in formula.lower():
            return False

    try:
        _eval_formula(formula, 100.0, {'test_rate': 1.0})
        return True
    except Exception:
        return False


def calculate_with_vat(price: Decimal, vat_included: bool, vat_rate: float = 1.2) -> Decimal:
    """
    Calculate price with VAT handling.

    Args:
        price: Base price
        vat_included: Whether VAT is already included
        vat_rate: VAT multiplier (default 1.2 = 20%)

    Returns:
        Price with VAT applied
    """
    if vat_included:
        return price
    return price * Decimal(str(vat_rate))