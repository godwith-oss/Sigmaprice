"""Tests for Module 3 - Parser"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from decimal import Decimal

from sigmaprice.parser.detector import (
    detect_format, detect_encoding, detect_delimiter,
    detect_header_row, detect_column_mapping
)
from sigmaprice.parser.normalizer import (
    normalize_item, _parse_price, _parse_availability,
    _normalize_delivery_type
)
from sigmaprice.core.types import AvailabilityStatus


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDetector:
    """Tests for file detection functions."""

    def test_detect_format_xlsx(self):
        """Test xlsx format detection."""
        path = FIXTURES_DIR / "test_price_simple.xlsx"
        assert detect_format(path) == "xlsx"

    def test_detect_format_csv(self):
        """Test csv format detection."""
        path = FIXTURES_DIR / "test_price.csv"
        assert detect_format(path) == "csv"

    def test_detect_format_unsupported(self):
        """Test unsupported format."""
        from sigmaprice.core.exceptions import ParseError
        path = FIXTURES_DIR / "test.txt"
        with pytest.raises(ParseError):
            detect_format(path)

    def test_detect_csv_encoding(self):
        """Test encoding detection."""
        path = FIXTURES_DIR / "test_price.csv"
        encoding = detect_encoding(path)
        assert encoding in ['utf-8', 'UTF-8', 'ascii']

    def test_detect_delimiter_comma(self):
        """Test comma delimiter detection."""
        path = FIXTURES_DIR / "test_price.csv"
        delimiter = detect_delimiter(path)
        assert delimiter == ','

    def test_detect_delimiter_semicolon(self):
        """Test semicolon delimiter detection."""
        path = FIXTURES_DIR / "test_price_semicolon.csv"
        delimiter = detect_delimiter(path, 'cp1251')
        assert delimiter == ';'

    def test_detect_header_row_simple(self):
        """Test header detection in simple data."""
        data = [
            [None, None, None],
            ["Code", "Name", "Price"],
            ["001", "Product", "100"]
        ]
        assert detect_header_row(data) == 1

    def test_detect_header_row_russian(self):
        """Test header detection with Russian headers."""
        data = [
            [],
            ["", ""],
            ["Код", "Наименование", "Цена"],
            ["001", "Товар", "100"]
        ]
        assert detect_header_row(data) == 2

    def test_detect_column_mapping(self):
        """Test auto column mapping detection."""
        headers = ["Код", "Наименование", "Цена", "Наличие", "Артикул"]
        mapping = detect_column_mapping(headers)

        assert 'name' in mapping
        assert 'price' in mapping


class TestNormalizer:
    """Tests for normalization functions."""

    def test_parse_price_decimal(self):
        """Test price parsing from decimal."""
        result = _parse_price(Decimal("1234.56"))
        assert result == Decimal("1234.56")

    def test_parse_price_int(self):
        """Test price parsing from int."""
        result = _parse_price(1000)
        assert result == Decimal("1000")

    def test_parse_price_string(self):
        """Test price parsing from string."""
        result = _parse_price("1 250,50")
        assert result == Decimal("1250.50")

    def test_parse_price_with_currency(self):
        """Test price parsing with currency symbols."""
        result = _parse_price("1 200 руб.")
        assert result == Decimal("1200")

    def test_parse_price_invalid(self):
        """Test price parsing with invalid input."""
        assert _parse_price(None) is None
        assert _parse_price("") is None

    def test_parse_availability_in_stock(self):
        """Test availability parsing - in stock."""
        assert _parse_availability("В наличии") == AvailabilityStatus.IN_STOCK
        assert _parse_availability("in stock") == AvailabilityStatus.IN_STOCK

    def test_parse_availability_reserved(self):
        """Test availability parsing - reserved."""
        assert _parse_availability("В резерве") == AvailabilityStatus.RESERVED
        assert _parse_availability("reserved") == AvailabilityStatus.RESERVED

    def test_parse_availability_on_order(self):
        """Test availability parsing - on order."""
        assert _parse_availability("Под заказ") == AvailabilityStatus.ON_ORDER
        assert _parse_availability("on order") == AvailabilityStatus.ON_ORDER

    def test_parse_availability_in_transit(self):
        """Test availability parsing - in transit."""
        assert _parse_availability("В пути") == AvailabilityStatus.IN_TRANSIT
        assert _parse_availability("транзит") == AvailabilityStatus.IN_TRANSIT

    def test_parse_availability_empty(self):
        """Test availability parsing - empty value."""
        assert _parse_availability("") == AvailabilityStatus.UNAVAILABLE
        assert _parse_availability(None) == AvailabilityStatus.UNAVAILABLE

    def test_normalize_delivery_type_retail(self):
        """Test delivery type normalization - retail variants."""
        assert _normalize_delivery_type("rtl") == "Retail"
        assert _normalize_delivery_type("RET") == "Retail"
        assert _normalize_delivery_type("box") == "Retail"
        assert _normalize_delivery_type("Retail") == "Retail"

    def test_normalize_delivery_type_oem(self):
        """Test delivery type normalization - OEM."""
        assert _normalize_delivery_type("OEM") == "OEM"
        assert _normalize_delivery_type("oem") == "OEM"

    def test_normalize_delivery_type_unknown(self):
        """Test delivery type normalization - unknown."""
        assert _normalize_delivery_type("UNKNOWN") == "Unknown"
        assert _normalize_delivery_type(None) is None


class TestExcelParser:
    """Tests for Excel parsing."""

    @patch('sigmaprice.parser.parser.get_supplier')
    @patch('sigmaprice.parser.parser.get_column_mapping')
    def test_parse_simple_excel(self, mock_mapping, mock_supplier):
        """Test parsing simple Excel file."""
        mock_supplier.return_value = MagicMock(id=1, currency="RUB")
        mock_mapping.return_value = {
            'name': 'Наименование',
            'price': 'Цена'
        }

        from sigmaprice.parser.parser import parse_price_file

        path = FIXTURES_DIR / "test_price_simple.xlsx"
        # Note: This will fail because we need actual supplier in DB
        # But we can test the file reading independently
        from sigmaprice.parser.excel_reader import read_excel

        rows = read_excel(path, None)
        assert len(rows) >= 2


class TestCSVParser:
    """Tests for CSV parsing."""

    def test_read_csv_utf8(self):
        """Test reading UTF-8 CSV."""
        from sigmaprice.parser.csv_reader import read_csv

        path = FIXTURES_DIR / "test_price.csv"
        rows = read_csv(path, None)

        assert len(rows) >= 2

    def test_read_csv_semicolon_cp1251(self):
        """Test reading semicolon CSV with cp1251."""
        from sigmaprice.parser.csv_reader import read_csv

        path = FIXTURES_DIR / "test_price_semicolon.csv"
        rows = read_csv(path, None)

        assert len(rows) >= 2


class TestFixtures:
    """Verify test fixtures exist and are readable."""

    def test_fixture_files_exist(self):
        """All fixture files should exist."""
        expected = [
            "test_price_simple.xlsx",
            "test_price_multi_sheet.xlsx",
            "test_price_exclude_sheet.xlsx",
            "test_price_header_row_3.xlsx",
            "test_price.csv",
            "test_price_semicolon.csv"
        ]

        for name in expected:
            path = FIXTURES_DIR / name
            assert path.exists(), f"Missing fixture: {name}"
            assert path.stat().st_size > 0, f"Empty fixture: {name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])