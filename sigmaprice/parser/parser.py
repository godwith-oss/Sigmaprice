"""Price file parser - main entry point"""
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sigmaprice.core.exceptions import ParseError
from sigmaprice.core.types import RawItem, AvailabilityStatus
from sigmaprice.core.logger import get_logger
from sigmaprice.parser.excel_reader import read_excel, get_sheet_names
from sigmaprice.parser.csv_reader import read_csv
from sigmaprice.parser.column_mapper import ColumnMapper, auto_detect_mapping
from sigmaprice.suppliers import get_supplier, get_column_mapping, should_exclude
from sigmaprice.suppliers.rules import get_rules

logger = get_logger(__name__)


class PriceParser:
    """Main price file parser."""

    def __init__(self, supplier_id: int):
        self.supplier_id = supplier_id
        self.supplier = get_supplier(supplier_id)
        if not self.supplier:
            raise ParseError(f"Supplier {supplier_id} not found")

        self.mapping = get_column_mapping(supplier_id)
        if not self.mapping:
            logger.warning(f"No column mapping for supplier {supplier_id}, will try auto-detect")

        self.rules = get_rules(supplier_id)

    def parse_file(self, file_path: Path) -> List[RawItem]:
        """
        Parse price file and return list of RawItem.

        Args:
            file_path: Path to price file (xlsx, xls, csv)

        Returns:
            List of parsed items

        Raises:
            ParseError: If parsing fails
        """
        logger.info(f"Parsing file: {file_path}")

        ext = file_path.suffix.lower()
        if ext in ['.xlsx', '.xls']:
            rows = read_excel(file_path)
        elif ext == '.csv':
            rows = read_csv(file_path)
        else:
            raise ParseError(f"Unsupported file format: {ext}")

        return self._process_rows(rows)

    def _process_rows(self, rows: List[Dict[str, Any]]) -> List[RawItem]:
        """Process all rows and convert to RawItem."""
        if not self.mapping:
            if rows:
                headers = list(rows[0].keys())
                self.mapping = auto_detect_mapping([h for h in headers if h != '_sheet'])
                logger.info(f"Auto-detected mapping: {self.mapping}")

        mapper = ColumnMapper(self.mapping) if self.mapping else None

        items = []
        skipped = 0

        for row in rows:
            try:
                mapped = mapper.map_row(row) if mapper else row
                item = self._row_to_raw_item(mapped)

                if item and not self._should_skip(item):
                    items.append(item)
                else:
                    skipped += 1

            except Exception as e:
                logger.warning(f"Failed to parse row: {e}")
                continue

        logger.info(f"Parsed: {len(items)} items, skipped: {skipped}")
        return items

    def _row_to_raw_item(self, row: Dict[str, Any]) -> Optional[RawItem]:
        """Convert mapped row to RawItem."""
        try:
            name = row.get('name')
            if not name:
                return None

            price_str = row.get('price')
            price = self._parse_price(price_str)

            return RawItem(
                supplier_id=self.supplier_id,
                supplier_code=str(row.get('code', '')),
                name=str(name),
                description=row.get('description'),
                price=price,
                currency=self.supplier.currency,
                availability=self._parse_availability(row.get('availability')),
                quantity=self._parse_int(row.get('quantity')),
                warranty_months=self._parse_int(row.get('warranty_months')),
                article=row.get('article'),
                ean=row.get('ean'),
                manufacturer=row.get('manufacturer'),
                delivery_type=row.get('delivery_type')
            )

        except Exception as e:
            logger.warning(f"Failed to convert row to RawItem: {e}")
            return None

    def _parse_price(self, value: Any) -> Decimal:
        """Parse price value to Decimal."""
        if value is None:
            return Decimal('0')

        if isinstance(value, (int, float)):
            return Decimal(str(value))

        if isinstance(value, str):
            value = value.strip().replace(' ', '').replace(',', '.')
            try:
                return Decimal(value)
            except:
                return Decimal('0')

        return Decimal('0')

    def _parse_availability(self, value: Any) -> AvailabilityStatus:
        """Parse availability status."""
        if not value:
            return AvailabilityStatus.UNAVAILABLE

        value = str(value).lower().strip()

        if 'наличии' in value or 'в наличи' in value or 'есть' in value or 'in stock' in value:
            return AvailabilityStatus.IN_STOCK
        elif 'резерв' in value or 'зарезервир' in value or 'reserved' in value:
            return AvailabilityStatus.RESERVED
        elif 'заказ' in value or 'под заказ' in value or 'on order' in value:
            return AvailabilityStatus.ON_ORDER
        elif 'транзит' in value or 'в пути' in value or 'in transit' in value or 'скоро' in value:
            return AvailabilityStatus.IN_TRANSIT
        else:
            return AvailabilityStatus.UNAVAILABLE

    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse integer value."""
        if value is None:
            return None

        try:
            return int(value)
        except:
            return None

    def _should_skip(self, item: RawItem) -> bool:
        """Check if item should be skipped due to rules."""
        return should_exclude(self.supplier_id, item)


def parse_price_file(supplier_id: int, file_path: Path) -> List[RawItem]:
    """
    Parse price file for a supplier.

    Main entry point for parsing.

    Args:
        supplier_id: Supplier ID
        file_path: Path to price file

    Returns:
        List of RawItem objects
    """
    parser = PriceParser(supplier_id)
    return parser.parse_file(file_path)