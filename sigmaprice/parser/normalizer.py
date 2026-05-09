"""Data normalization for parsed price items"""
from decimal import Decimal
from typing import Dict, Any, Optional
from sigmaprice.core.types import RawItem, AvailabilityStatus
from sigmaprice.core.constants import RETAIL_ALIASES, OEM_ALIASES
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def normalize_item(raw_data: Dict[str, Any], supplier) -> Optional[RawItem]:
    """
    Transform raw dictionary from parser into RawItem object.

    Performs:
    - Lowercase conversion where needed
    - Whitespace trimming
    - Price parsing (removing currency symbols, spaces)
    - Availability status parsing to enum
    - Delivery type normalization (rtl → Retail, etc.)
    - Currency from supplier record

    Args:
        raw_data: Dictionary with keys from column mapping (our field names)
        supplier: Supplier object from DB

    Returns:
        RawItem object or None if required fields missing
    """
    try:
        name = _normalize_string(raw_data.get('name'))
        if not name:
            logger.warning("Missing required field: name")
            return None

        price = _parse_price(raw_data.get('price'))
        if price is None or price <= 0:
            logger.warning(f"Invalid price for item: {name}")
            return None

        return RawItem(
            supplier_id=supplier.id,
            supplier_code=_normalize_string(raw_data.get('code')) or '',
            name=name,
            description=_normalize_string(raw_data.get('description')),
            price=price,
            currency=supplier.currency,
            availability=_parse_availability(raw_data.get('availability')),
            quantity=_parse_int(raw_data.get('quantity')),
            warranty_months=_parse_int(raw_data.get('warranty_months')),
            article=_normalize_string(raw_data.get('article')),
            ean=_normalize_string(raw_data.get('ean')),
            manufacturer=_normalize_string(raw_data.get('manufacturer')),
            delivery_type=_normalize_delivery_type(raw_data.get('delivery_type'))
        )

    except Exception as e:
        logger.error(f"Normalization error: {e}")
        return None


def _normalize_string(value: Any) -> Optional[str]:
    """Normalize string value - trim and clean."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _parse_price(value: Any) -> Optional[Decimal]:
    """Parse price string to Decimal."""
    if value is None:
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(str(value))

    if isinstance(value, str):
        value = value.strip()
        value = value.replace(' ', '').replace('\xa0', '')
        value = value.replace('₽', '').replace('руб', '').replace('р.', '')
        value = value.replace(',', '.').replace('$', '').replace('€', '')
        value = value.replace('USD', '').replace('EUR', '').replace('RUB', '')

        try:
            return Decimal(value)
        except:
            return None

    return None


def _parse_availability(value: Any) -> AvailabilityStatus:
    """Parse availability string to enum."""
    if not value:
        return AvailabilityStatus.UNAVAILABLE

    value = str(value).lower().strip()

    if any(x in value for x in ['наличии', 'в наличи', 'есть', 'in stock', 'ready', 'склад']):
        return AvailabilityStatus.IN_STOCK
    elif any(x in value for x in ['резерв', 'reserved', 'бронир']):
        return AvailabilityStatus.RESERVED
    elif any(x in value for x in ['заказ', 'под заказ', 'on order', 'order']):
        return AvailabilityStatus.ON_ORDER
    elif any(x in value for x in ['транзит', 'в пути', 'in transit', 'скоро', 'ожида']):
        return AvailabilityStatus.IN_TRANSIT
    else:
        return AvailabilityStatus.UNAVAILABLE


def _parse_int(value: Any) -> Optional[int]:
    """Parse integer value."""
    if value is None:
        return None
    try:
        return int(value)
    except:
        return None


def _normalize_delivery_type(value: Any) -> Optional[str]:
    """Normalize delivery type to standard values."""
    if not value:
        return None

    value = str(value).lower().strip()

    for alias in RETAIL_ALIASES:
        if alias in value:
            return 'Retail'

    for alias in OEM_ALIASES:
        if alias in value:
            return 'OEM'

    if value in ['retail', 'rtl', 'ret', 'box']:
        return 'Retail'
    if value == 'oem':
        return 'OEM'

    return 'Unknown'


def normalize_article(article: Optional[str]) -> Optional[str]:
    """Normalize article number - trim spaces, upper case."""
    if not article:
        return None
    article = str(article).strip().upper()
    return article if article else None


def normalize_ean(ean: Optional[str]) -> Optional[str]:
    """Normalize EAN/UPC - keep only digits."""
    if not ean:
        return None
    ean = ''.join(c for c in str(ean) if c.isdigit())
    return ean if len(ean) >= 8 else None