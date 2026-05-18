"""Export data builder — query catalog items with user permissions"""
from typing import List, Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sigmaprice.db.models import (
    CatalogItem, Category, Supplier, SupplierItem, SupplierItemMapping
)
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def build_export_data(
    user_id: int,
    max_suppliers: int = 10,
    session: Optional[Session] = None,
) -> tuple[List[Dict], List[str]]:
    """
    Build export data for a user with permission filtering.

    Returns:
        tuple of (rows: List[Dict], supplier_headers: List[str])

    Each row dict has keys:
        category, manufacturer, reserve1, reserve2, code, name,
        description, our_price, rrp, warranty_months, article, ean,
        supplier_1_price, supplier_1_available, supplier_2_price, ...
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    from sigmaprice.auth.permissions import get_allowed_categories, get_allowed_suppliers

    allowed_categories = get_allowed_categories(user_id, session)
    allowed_suppliers = get_allowed_suppliers(user_id, session)

    query = session.query(CatalogItem).join(
        Category, CatalogItem.category_id == Category.id
    )

    if allowed_categories is not None:
        query = query.filter(CatalogItem.category_id.in_(allowed_categories))
    else:
        query = query.filter(CatalogItem.category_id.isnot(None))

    query = query.filter(CatalogItem.our_price.isnot(None))

    catalog_items = query.order_by(
        Category.name,
        CatalogItem.manufacturer,
        CatalogItem.our_price.asc(),
    ).all()

    supplier_ids = _get_export_suppliers(allowed_suppliers, session, max_suppliers)
    supplier_headers = _build_supplier_headers(supplier_ids, session)

    category_map = _build_category_map(session)

    rows = []
    for item in catalog_items:
        category_path = _get_category_path(item.category_id, category_map)

        row = {
            "category": category_path,
            "manufacturer": item.manufacturer or "",
            "reserve1": "",
            "reserve2": "",
            "code": item.code,
            "name": item.name,
            "description": item.description or "",
            "our_price": item.our_price,
            "rrp": item.rrp,
            "warranty_months": item.warranty_months,
            "article": item.article or "",
            "ean": item.ean or "",
        }

        for i, supplier_id in enumerate(supplier_ids, start=1):
            si = _get_supplier_item(item.id, supplier_id, session)
            row[f"supplier_{i}_price"] = si.price_calculated if si else None
            row[f"supplier_{i}_available"] = si.availability.value if si else ""

        rows.append(row)

    logger.info(
        f"Built export data: {len(rows)} items, "
        f"{len(supplier_ids)} suppliers for user {user_id}"
    )
    return rows, supplier_headers


def _get_export_suppliers(
    allowed_suppliers: Optional[List[int]],
    session: Session,
    max_suppliers: int,
) -> List[int]:
    """Get list of supplier IDs for export, limited to max_suppliers."""
    query = session.query(Supplier).order_by(Supplier.name.asc())

    if allowed_suppliers is not None:
        query = query.filter(Supplier.id.in_(allowed_suppliers))

    suppliers = query.limit(max_suppliers).all()
    return [s.id for s in suppliers]


def _build_supplier_headers(
    supplier_ids: List[int],
    session: Session,
) -> List[str]:
    """Build header names for supplier columns."""
    suppliers = {
        s.id: s.name
        for s in session.query(Supplier).filter(Supplier.id.in_(supplier_ids)).all()
    }
    headers = []
    for sid in supplier_ids:
        name = suppliers.get(sid, f"Поставщик {sid}")
        headers.append(f"{name} (цена)")
        headers.append(f"{name} (наличие)")
    return headers


def _get_category_path(category_id: int, category_map: Dict[int, str]) -> str:
    """Get full category path like 'Видеокарты/NVIDIA'."""
    return category_map.get(category_id, "")


def _build_category_map(session: Session) -> Dict[int, str]:
    """Build category ID -> path mapping."""
    categories = session.query(Category).all()
    cat_dict = {c.id: c for c in categories}

    result = {}
    for cat in categories:
        path_parts = []
        current = cat
        while current:
            path_parts.append(current.name)
            current = cat_dict.get(current.parent_id) if current.parent_id else None
        result[cat.id] = "/".join(reversed(path_parts))

    return result


def _get_supplier_item(
    catalog_item_id: int,
    supplier_id: int,
    session: Session,
) -> Optional[SupplierItem]:
    """Get supplier item for a specific catalog item and supplier."""
    return session.query(SupplierItem).filter(
        SupplierItem.catalog_item_id == catalog_item_id,
        SupplierItem.supplier_id == supplier_id,
    ).first()
