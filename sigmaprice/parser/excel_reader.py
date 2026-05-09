"""Excel file reader for price lists"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import openpyxl
from sigmaprice.core.exceptions import ParseError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def read_excel(file_path: Path) -> List[Dict[str, Any]]:
    """
    Read Excel file (xlsx/xls) and return list of rows.

    Args:
        file_path: Path to Excel file

    Returns:
        List of dictionaries, one per row

    Raises:
        ParseError: If file cannot be read
    """
    if not file_path.exists():
        raise ParseError(f"File not found: {file_path}")

    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
    except Exception as e:
        raise ParseError(f"Failed to open Excel file: {e}")

    all_rows = []

    for sheet_name in workbook.sheetnames:
        logger.info(f"Processing sheet: {sheet_name}")
        sheet = workbook[sheet_name]

        headers = _get_headers(sheet)
        if not headers:
            logger.warning(f"Empty sheet: {sheet_name}")
            continue

        rows = _read_sheet_rows(sheet, headers, sheet_name)
        all_rows.extend(rows)

    logger.info(f"Total rows read: {len(all_rows)}")
    return all_rows


def _get_headers(sheet) -> Optional[List[str]]:
    """Get header row from sheet."""
    for row in sheet.iter_rows(max_row=1, values_only=True):
        if row and any(cell for cell in row):
            return [str(cell).strip() if cell else "" for cell in row]
    return None


def _read_sheet_rows(sheet, headers: List[str], sheet_name: str) -> List[Dict[str, Any]]:
    """Read all rows from a single sheet."""
    rows = []

    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not any(cell for cell in row):
            continue

        row_dict = {"_sheet": sheet_name}
        for col_idx, header in enumerate(headers):
            if col_idx < len(row):
                value = row[col_idx]
                row_dict[header] = _clean_value(value)

        rows.append(row_dict)

    return rows


def _clean_value(value: Any) -> Any:
    """Clean cell value."""
    if value is None:
        return None

    if isinstance(value, str):
        return value.strip()

    return value


def get_sheet_names(file_path: Path) -> List[str]:
    """Get list of sheet names in Excel file."""
    workbook = openpyxl.load_workbook(file_path, read_only=True)
    return workbook.sheetnames