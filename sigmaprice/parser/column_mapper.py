"""Column mapping for parsing supplier price files"""
from typing import Dict, Optional, Any, Callable
from sigmaprice.core.exceptions import ParseError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


class ColumnMapper:
    """Maps supplier's column names to our internal fields."""

    STANDARD_FIELDS = [
        'code', 'name', 'description', 'price', 'availability',
        'quantity', 'warranty_months', 'article', 'ean', 'manufacturer',
        'delivery_type', 'category', 'product_url', 'country_origin'
    ]

    def __init__(self, mapping: Dict[str, str]):
        """
        Initialize with supplier's column mapping.

        Args:
            mapping: Dict of our_field -> supplier_column
                Example: {'code': 'Код', 'name': 'Наименование', ...}
        """
        self.mapping = mapping
        self.reverse_mapping = {v: k for k, v in mapping.items()}

    def map_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a row from supplier format to our format.

        Args:
            row: Row from supplier's price file

        Returns:
            Mapped row with our field names
        """
        result = {}

        for our_field, supplier_col in self.mapping.items():
            value = row.get(supplier_col) or row.get(supplier_col.lower()) or row.get(self._normalize_key(supplier_col))
            result[our_field] = value

        return result

    def _normalize_key(self, key: str) -> str:
        """Normalize key for case-insensitive matching."""
        return key.lower().strip().replace('_', ' ').replace('-', ' ')

    def validate_mapping(self) -> bool:
        """Validate that mapping contains required fields."""
        required = ['name', 'price']
        for field in required:
            if field not in self.mapping:
                logger.warning(f"Missing required field in mapping: {field}")
                return False
        return True

    def get_missing_fields(self) -> list[str]:
        """Get list of fields not mapped."""
        return [f for f in self.STANDARD_FIELDS if f not in self.mapping]


def normalize_column_name(name: str) -> str:
    """Normalize column name for matching."""
    if not name:
        return ""

    name = name.lower().strip()
    name = name.replace('_', ' ').replace('-', ' ')
    name = name.replace('ё', 'е').replace('Ё', 'Е')

    return name


def auto_detect_mapping(
    headers: list[str],
    field_patterns: Optional[Dict[str, list[str]]] = None
) -> Dict[str, str]:
    """
    Auto-detect column mapping based on header names.

    Args:
        headers: List of column headers from price file
        field_patterns: Optional dict of field -> patterns to match

    Returns:
        Dict of our_field -> detected column
    """
    if field_patterns is None:
        field_patterns = {
            'code': ['код', 'sku', 'id', 'артикул'],
            'name': ['наименование', 'название', 'товар', 'product', 'name'],
            'description': ['описание', 'desc', 'детали'],
            'price': ['цена', 'price', 'стоимость', 'сумма'],
            'availability': ['наличие', 'статус', 'availability', 'в наличии'],
            'quantity': ['количество', 'qty', 'остаток', 'кол-во'],
            'warranty': ['гарантия', 'warranty'],
            'article': ['артикул', 'модель', 'part number', 'pn'],
            'ean': ['ean', 'upc', 'штрих', 'barcode'],
            'manufacturer': ['производитель', 'brand', 'vendor', 'изготовитель'],
            'delivery_type': ['тип', 'поставка', 'delivery', 'тип поставки'],
            'category': ['категория', 'группа', 'category', 'раздел'],
        }

    mapping = {}
    normalized_headers = {normalize_column_name(h): h for h in headers}

    for field, patterns in field_patterns.items():
        for pattern in patterns:
            for norm_header, original_header in normalized_headers.items():
                if pattern in norm_header:
                    mapping[field] = original_header
                    break
            if field in mapping:
                break

    logger.info(f"Auto-detected mapping: {mapping}")
    return mapping