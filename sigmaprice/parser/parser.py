"""Price file parser - main entry point

This is the ONLY function other modules call. Rest are internal.
"""
from pathlib import Path
from typing import List
from sigmaprice.core.exceptions import ParseError, SupplierError
from sigmaprice.core.types import RawItem
from sigmaprice.core.logger import get_logger
from sigmaprice.parser.excel_reader import read_excel
from sigmaprice.parser.csv_reader import read_csv
from sigmaprice.parser.detector import detect_format
from sigmaprice.parser.normalizer import normalize_item
from sigmaprice.suppliers import get_supplier, get_column_mapping
from sigmaprice.suppliers.rules import should_exclude

logger = get_logger(__name__)


def parse_price_file(file_path: Path, supplier_id: int) -> List[RawItem]:
    """
    Parse supplier price file and return list of normalized items.

    Algorithm:
    1. Get supplier settings from DB (Module 2)
    2. Detect file format (xlsx/csv)
    3. Read all sheets (Excel) or entire file (CSV)
    4. For each sheet:
       - Check exclude_sheet rule - skip if needed
       - Detect header row
       - Read data with column mapping
    5. For each item:
       - Apply exclusion rules (exclude_category, keyword, price_range)
       - If item passes all rules - normalize and add to result
    6. Return list of RawItem

    Args:
        file_path: Path to price file
        supplier_id: Supplier ID

    Returns:
        List of RawItem objects

    Raises:
        ParseError: If file corrupted or format not supported
        SupplierError: If supplier_id not found in DB
    """
    supplier = get_supplier(supplier_id)
    if not supplier:
        raise SupplierError(f"Supplier {supplier_id} not found")

    logger.info(f"Parsing file: {file_path} for supplier {supplier_id}")

    column_map = get_column_mapping(supplier_id)
    if not column_map:
        logger.warning(f"No column mapping for supplier {supplier_id}, will auto-detect")

    file_format = detect_format(file_path)

    if file_format in ['xlsx', 'xls']:
        rows = read_excel(file_path, column_map)
    elif file_format == 'csv':
        rows = read_csv(file_path, column_map)
    else:
        raise ParseError(f"Unsupported format: {file_format}")

    return _process_items(rows, supplier)


def _process_items(rows: list, supplier) -> list[RawItem]:
    """Process parsed rows, apply rules and normalize."""
    items = []
    skipped = 0

    for row in rows:
        try:
            raw_item = normalize_item(row, supplier)

            if raw_item is None:
                skipped += 1
                continue

            if should_exclude(supplier.id, raw_item):
                skipped += 1
                continue

            items.append(raw_item)

        except Exception as e:
            logger.warning(f"Failed to process row: {e}")
            skipped += 1
            continue

    logger.info(f"Parsed: {len(items)} items, skipped: {skipped}")
    return items