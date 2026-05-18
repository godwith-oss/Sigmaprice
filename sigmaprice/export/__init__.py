"""Export module — catalog export to Excel/CSV with user permissions"""
from pathlib import Path
from typing import Literal
from sigmaprice.export.builder import build_export_data
from sigmaprice.export.excel_writer import write_excel
from sigmaprice.export.csv_writer import write_csv
from sigmaprice.core.exceptions import ValidationError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)

__all__ = ["export_catalog"]


def export_catalog(
    user_id: int,
    format: Literal["xlsx", "csv"] = "xlsx",
    max_suppliers: int = 10,
) -> Path:
    """
    Create a catalog export for a user with permission filtering.

    Args:
        user_id: User ID (from Module 8)
        format: 'xlsx' or 'csv'
        max_suppliers: Maximum suppliers in export (1-10, default 10)

    Returns:
        Path to created file.
        Location: /tmp/exports/catalog_{user_id}_{timestamp}.{format}

    Raises:
        ValueError: If user not found
        PermissionError: If user has no export rights
    """
    from sigmaprice.auth import get_user, get_allowed_categories, get_allowed_suppliers
    from sigmaprice.core.database import get_session
    from datetime import datetime
    import os

    if max_suppliers < 1 or max_suppliers > 10:
        raise ValidationError("max_suppliers must be between 1 and 10")

    session = get_session()

    user = get_user(user_id, session)
    if not user:
        raise ValueError(f"User {user_id} not found")

    if not user.is_active:
        raise PermissionError(f"User {user_id} is inactive")

    export_dir = Path("/tmp/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"catalog_{user_id}_{timestamp}.{format}"
    filepath = export_dir / filename

    rows, supplier_headers = build_export_data(
        user_id=user_id,
        max_suppliers=max_suppliers,
        session=session,
    )

    if format == "xlsx":
        write_excel(rows, supplier_headers, filepath)
    else:
        write_csv(rows, supplier_headers, filepath)

    logger.info(
        f"Catalog export complete: {filepath} "
        f"(user={user_id}, rows={len(rows)}, suppliers={len(supplier_headers)//2})"
    )
    return filepath
