"""Validators for catalog item fields"""
import re
from typing import Optional
from sqlalchemy.orm import Session
from sigmaprice.core.exceptions import ValidationError

DELIVERY_TYPE_VALUES = {"OEM", "Retail"}
OEM_SYNONYMS = {"oem", "tray"}
RETAIL_SYNONYMS = {"box", "rtl", "ret", "retail"}


def validate_name(name: str) -> str:
    """Validate and normalize item name."""
    if not name or not name.strip():
        raise ValidationError("Item name cannot be empty")

    name = name.strip()
    name = re.sub(r'\s+', ' ', name)

    if len(name) < 3:
        raise ValidationError("Item name must be at least 3 characters")

    return name


def validate_code(code: str) -> str:
    """Validate catalog item code format."""
    if not code or not re.match(r'^[1-9]\d{7}$', code):
        raise ValidationError(
            "Code must be exactly 8 digits, not starting with 0"
        )
    return code


def validate_ean(ean: Optional[str]) -> Optional[str]:
    """Validate EAN/UPC barcode."""
    if ean is None:
        return None
    ean = ean.strip()
    if not ean:
        return None
    if not re.match(r'^\d{8,14}$', ean):
        raise ValidationError(f"Invalid EAN/UPC: {ean}")
    return ean


def determine_delivery_type(item_name: str, raw_delivery_type: Optional[str] = None) -> Optional[str]:
    """
    Determine delivery type (OEM vs Retail) from item data.

    Returns:
        "OEM", "Retail", or None (cannot determine)
    """
    if raw_delivery_type:
        raw_lower = raw_delivery_type.strip().lower()

        if raw_lower in OEM_SYNONYMS:
            return "OEM"
        if raw_lower in RETAIL_SYNONYMS:
            return "Retail"

    name_lower = item_name.lower()

    for oem_term in OEM_SYNONYMS:
        if f' {oem_term}' in name_lower or name_lower.startswith(f'{oem_term} '):
            return "OEM"

    for retail_term in ("box", "retail"):
        if f' {retail_term}' in name_lower or name_lower.startswith(f'{retail_term} '):
            return "Retail"

    return None


def is_excluded_delivery(item_name: str, session: Optional[Session] = None) -> bool:
    """
    Check if item should be excluded due to damaged/defective packaging.
    Reads exclusion patterns from knowledge_base table.
    """
    from sigmaprice.knowledge import is_excluded_by_kb
    return is_excluded_by_kb(item_name, session)
