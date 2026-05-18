"""CSV writer for catalog export"""
from pathlib import Path
from typing import List, Dict
import csv
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)

STATIC_COLUMNS = [
    "Категория",
    "Производитель",
    "Резерв 1",
    "Резерв 2",
    "Код",
    "Наименование",
    "Описание",
    "Наша цена (₽)",
    "РРЦ (₽)",
    "Гарантия (мес)",
    "Артикул",
    "EAN/UPC",
]

FIELD_MAP = {
    "Категория": "category",
    "Производитель": "manufacturer",
    "Резерв 1": "reserve1",
    "Резерв 2": "reserve2",
    "Код": "code",
    "Наименование": "name",
    "Описание": "description",
    "Наша цена (₽)": "our_price",
    "РРЦ (₽)": "rrp",
    "Гарантия (мес)": "warranty_months",
    "Артикул": "article",
    "EAN/UPC": "ean",
}


def write_csv(
    rows: List[Dict],
    supplier_headers: List[str],
    filepath: Path,
) -> Path:
    """
    Write export data to CSV.

    Spec: UTF-8 with BOM, delimiter ';', decimal comma.

    Args:
        rows: List of row dicts from builder
        supplier_headers: List of supplier column names
        filepath: Output file path

    Returns:
        Path to created file
    """
    all_headers = STATIC_COLUMNS + supplier_headers

    price_fields = {"Наша цена (₽)", "РРЦ (₽)"}
    price_fields.update({h for h in supplier_headers if "(цена)" in h})

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        writer.writerow(all_headers)

        for row_data in rows:
            csv_row = []

            for header in STATIC_COLUMNS:
                field = FIELD_MAP.get(header, header.lower())
                value = row_data.get(field, "")

                if header in price_fields and value is not None:
                    value = _format_price_csv(value)

                csv_row.append(value if value is not None else "")

            for i, supplier_header in enumerate(supplier_headers):
                is_price = "(цена)" in supplier_header
                key_base = f"supplier_{i // 2 + 1}"

                if is_price:
                    value = row_data.get(f"{key_base}_price")
                    if value is not None:
                        value = _format_price_csv(value)
                else:
                    value = row_data.get(f"{key_base}_available", "")

                csv_row.append(value if value is not None else "")

            writer.writerow(csv_row)

    logger.info(f"CSV export saved: {filepath} ({len(rows)} rows)")
    return filepath


def _format_price_csv(value) -> str:
    """Format price with comma as decimal separator: 1234,56"""
    return f"{value:.2f}".replace(".", ",")
