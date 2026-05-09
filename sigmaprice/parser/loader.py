"""Price loader - orchestrates full import process"""
from pathlib import Path
from typing import List, Optional, Dict
from decimal import Decimal
from sigmaprice.core.exceptions import ParseError, CatalogError
from sigmaprice.core.logger import get_logger
from sigmaprice.core.types import RawItem, AvailabilityStatus
from sigmaprice.parser.parser import PriceParser, parse_price_file
from sigmaprice.db.models import SupplierItem, CatalogItem, SupplierItemMapping
from sigmaprice.suppliers import calculate_price, get_supplier
from sigmaprice.core.database import create_session
from sigmaprice.catalog.items import get_item_by_code, create_catalog_item

logger = get_logger(__name__)


class PriceLoader:
    """Orchestrates full price import process."""

    def __init__(self, supplier_id: int):
        self.supplier_id = supplier_id
        self.supplier = get_supplier(supplier_id)
        if not self.supplier:
            raise ParseError(f"Supplier {supplier_id} not found")

        self.upload_number = self._get_next_upload_number()

    def _get_next_upload_number(self) -> int:
        """Get next upload number for this supplier."""
        session = create_session()
        try:
            from sigmaprice.db.models import SupplierItem
            last_item = session.query(SupplierItem).filter(
                SupplierItem.supplier_id == self.supplier_id
            ).order_by(SupplierItem.last_seen_at.desc()).first()

            return (last_item.upload_number + 1) if last_item else 1
        finally:
            session.close()

    def load_price_file(self, file_path: Path) -> Dict[str, int]:
        """
        Load price file and update database.

        Args:
            file_path: Path to price file

        Returns:
            Dict with stats: created, updated, skipped, errors
        """
        logger.info(f"Loading price file from {file_path}")

        items = parse_price_file(self.supplier_id, file_path)

        session = create_session()
        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        try:
            for item in items:
                try:
                    self._process_item(item, session)
                    stats['updated'] += 1
                except Exception as e:
                    logger.error(f"Failed to process item {item.supplier_code}: {e}")
                    stats['errors'] += 1

            session.commit()
            logger.info(f"Load complete: {stats}")

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to load price file: {e}")
            raise

        finally:
            session.close()

        return stats

    def _process_item(self, item: RawItem, session) -> None:
        """Process single item - update or create."""
        mapping = session.query(SupplierItemMapping).filter(
            SupplierItemMapping.supplier_id == self.supplier_id,
            SupplierItemMapping.supplier_code == item.supplier_code
        ).first()

        if mapping:
            self._update_existing_item(item, mapping.catalog_item_id, session)
        else:
            self._create_new_item(item, session)

    def _update_existing_item(self, item: RawItem, catalog_item_id: int, session) -> None:
        """Update existing supplier item."""
        supplier_item = session.query(SupplierItem).filter(
            SupplierItem.supplier_id == self.supplier_id,
            SupplierItem.catalog_item_id == catalog_item_id,
            SupplierItem.supplier_code == item.supplier_code
        ).first()

        price = calculate_price(
            self.supplier_id,
            item.price,
            session=session
        )

        if supplier_item:
            supplier_item.price_original = item.price
            supplier_item.price_calculated = price
            supplier_item.availability = item.availability
            supplier_item.quantity = item.quantity
            supplier_item.warranty_months = item.warranty_months
        else:
            supplier_item = SupplierItem(
                supplier_id=self.supplier_id,
                supplier_code=item.supplier_code,
                catalog_item_id=catalog_item_id,
                price_original=item.price,
                price_calculated=price,
                availability=item.availability,
                quantity=item.quantity,
                warranty_months=item.warranty_months,
                upload_number=self.upload_number
            )
            session.add(supplier_item)

    def _create_new_item(self, item: RawItem, session) -> None:
        """Create new item in catalog and supplier_items."""
        catalog_item = create_catalog_item(
            name=item.name,
            description=item.description,
            manufacturer=item.manufacturer,
            article=item.article,
            ean=item.ean,
            delivery_type=item.delivery_type,
            session=session
        )

        price = calculate_price(
            self.supplier_id,
            item.price,
            session=session
        )

        supplier_item = SupplierItem(
            supplier_id=self.supplier_id,
            supplier_code=item.supplier_code,
            catalog_item_id=catalog_item.id,
            price_original=item.price,
            price_calculated=price,
            availability=item.availability,
            quantity=item.quantity,
            warranty_months=item.warranty_months,
            upload_number=self.upload_number
        )
        session.add(supplier_item)

        mapping = SupplierItemMapping(
            catalog_item_id=catalog_item.id,
            supplier_id=self.supplier_id,
            supplier_code=item.supplier_code
        )
        session.add(mapping)


def load_price(supplier_id: int, file_path: Path) -> Dict[str, int]:
    """
    Load price file for supplier.

    Main entry point.

    Args:
        supplier_id: Supplier ID
        file_path: Path to price file

    Returns:
        Dict with stats
    """
    loader = PriceLoader(supplier_id)
    return loader.load_price_file(file_path)