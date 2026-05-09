"""CSV file reader for price lists"""
from pathlib import Path
from typing import Dict, List, Optional
import csv
from sigmaprice.core.exceptions import ParseError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def read_csv(
    file_path: Path,
    encoding: str = "utf-8",
    delimiter: str = ",",
    skip_empty_lines: bool = True
) -> List[Dict[str, str]]:
    """
    Read CSV file and return list of rows.

    Args:
        file_path: Path to CSV file
        encoding: File encoding (default: utf-8)
        delimiter: Field delimiter (default: ,)
        skip_empty_lines: Skip empty lines

    Returns:
        List of dictionaries, one per row

    Raises:
        ParseError: If file cannot be read
    """
    if not file_path.exists():
        raise ParseError(f"File not found: {file_path}")

    try:
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            return _parse_csv(f, delimiter, skip_empty_lines)
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='cp1251', newline='') as f:
                return _parse_csv(f, delimiter, skip_empty_lines)
        except Exception as e:
            raise ParseError(f"Failed to read CSV file: {e}")
    except Exception as e:
        raise ParseError(f"Failed to read CSV file: {e}")


def _parse_csv(f, delimiter: str, skip_empty_lines: bool) -> List[Dict[str, str]]:
    """Parse CSV file content."""
    reader = csv.DictReader(f, delimiter=delimiter, skip_blank_lines=skip_empty_lines)

    rows = []
    for row in reader:
        cleaned = {k.strip(): _clean_value(v) for k, v in row.items() if k.strip()}
        if cleaned:
            rows.append(cleaned)

    logger.info(f"CSV rows read: {len(rows)}")
    return rows


def _clean_value(value: Optional[str]) -> Optional[str]:
    """Clean cell value."""
    if value is None:
        return None

    value = value.strip()
    if value == "":
        return None

    return value


def detect_delimiter(file_path: Path) -> str:
    """Detect CSV delimiter by analyzing first few lines."""
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        sample = f.read(4096)

    comma_count = sample.count(',')
    semicolon_count = sample.count(';')
    tab_count = sample.count('\t')

    if comma_count >= semicolon_count and comma_count >= tab_count:
        return ','
    elif semicolon_count >= tab_count:
        return ';'
    else:
        return '\t'