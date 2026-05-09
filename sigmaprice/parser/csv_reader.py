"""CSV file reader for price lists"""
from pathlib import Path
from typing import Dict, List, Optional
import csv
import chardet
from sigmaprice.core.exceptions import ParseError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def read_csv(
    file_path: Path,
    column_map: Optional[Dict[str, str]] = None
) -> List[Dict[str, str]]:
    """
    Read CSV file with auto-detection of encoding and delimiter.

    Args:
        file_path: Path to CSV file
        column_map: Dict of our_field -> supplier_column
            If provided, data will be mapped to our field names.

    Returns:
        List of dictionaries with normalized keys

    Raises:
        ParseError: If file cannot be read
    """
    if not file_path.exists():
        raise ParseError(f"File not found: {file_path}")

    encoding = _detect_encoding(file_path)
    delimiter = _detect_delimiter(file_path, encoding)

    try:
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = list(reader)
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='cp1251', newline='') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)
        except Exception as e:
            raise ParseError(f"Failed to read CSV file: {e}")
    except Exception as e:
        raise ParseError(f"Failed to read CSV file: {e}")

    reverse_map = {}
    if column_map:
        reverse_map = {v: k for k, v in column_map.items()}

    result = []
    for row in rows:
        cleaned = {}
        for k, v in row.items():
            if not k:
                continue

            k_clean = k.strip()
            v_clean = v.strip() if v else ''

            if column_map:
                mapped_key = reverse_map.get(k_clean, k_clean)
            else:
                mapped_key = k_clean

            if v_clean:
                cleaned[mapped_key] = v_clean

        # Check if row has any data
        if cleaned:
            result.append(cleaned)

    logger.info(f"CSV rows read: {len(result)}")
    return result


def _detect_encoding(file_path: Path) -> str:
    """Detect file encoding."""
    try:
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read(10000))
            encoding = result['encoding'] or 'utf-8'
            logger.info(f"Detected encoding: {encoding}")
            return encoding
    except Exception as e:
        logger.warning(f"Failed to detect encoding: {e}")
        return 'utf-8'


def _detect_delimiter(file_path: Path, encoding: str) -> str:
    """Detect CSV delimiter."""
    try:
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            sample = f.read(4096)

        comma = sample.count(',')
        semicolon = sample.count(';')
        tab = sample.count('\t')

        if semicolon > comma and semicolon >= tab:
            return ';'
        if tab > comma and tab >= semicolon:
            return '\t'
        return ','

    except Exception as e:
        logger.warning(f"Failed to detect delimiter: {e}")
        return ','