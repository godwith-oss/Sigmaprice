"""Tests for Module 7 - Export"""
import pytest
from pathlib import Path
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sigmaprice.export import export_catalog
from sigmaprice.export.builder import (
    build_export_data,
    _get_export_suppliers,
    _build_category_map,
    _get_category_path,
)
from sigmaprice.export.excel_writer import write_excel
from sigmaprice.export.csv_writer import write_csv
from sigmaprice.core.exceptions import ValidationError


class TestExportCatalog:
    """Test export_catalog public API."""

    @patch('sigmaprice.core.database.get_session')
    def test_user_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        with patch('sigmaprice.auth.get_user', return_value=None):
            with pytest.raises(ValueError, match="not found"):
                export_catalog(user_id=999)

    @patch('sigmaprice.core.database.get_session')
    def test_inactive_user(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_user = MagicMock()
        mock_user.is_active = False
        mock_user.id = 5

        with patch('sigmaprice.auth.get_user', return_value=mock_user):
            with pytest.raises(PermissionError, match="inactive"):
                export_catalog(user_id=5)

    @patch('sigmaprice.core.database.get_session')
    def test_invalid_max_suppliers(self, mock_get_session):
        mock_get_session.return_value = MagicMock()

        mock_user = MagicMock()
        mock_user.is_active = True

        with patch('sigmaprice.auth.get_user', return_value=mock_user):
            with pytest.raises(ValidationError, match="max_suppliers"):
                export_catalog(user_id=1, max_suppliers=0)

            with pytest.raises(ValidationError, match="max_suppliers"):
                export_catalog(user_id=1, max_suppliers=11)


class TestBuilder:
    """Test export data builder."""

    def test_export_suppliers_limits(self):
        session = MagicMock()
        supp1 = MagicMock()
        supp1.id = 1
        supp2 = MagicMock()
        supp2.id = 2

        q3 = MagicMock()
        q3.all.return_value = [supp1, supp2]

        q2 = MagicMock()
        q2.limit.return_value = q3

        q1 = MagicMock()
        q1.order_by.return_value = q2

        session.query.return_value = q1

        result = _get_export_suppliers(
            allowed_suppliers=None,
            session=session,
            max_suppliers=2,
        )

        assert len(result) == 2
        assert result == [1, 2]

    def test_export_suppliers_with_filter(self):
        session = MagicMock()
        supp1 = MagicMock()
        supp1.id = 3

        q4 = MagicMock()
        q4.all.return_value = [supp1]

        q3 = MagicMock()
        q3.limit.return_value = q4

        q2 = MagicMock()
        q2.filter.return_value = q3

        q1 = MagicMock()
        q1.order_by.return_value = q2

        session.query.return_value = q1

        result = _get_export_suppliers(
            allowed_suppliers=[3, 5],
            session=session,
            max_suppliers=10,
        )

        assert result == [3]

    def test_category_path_simple(self):
        cat_map = {1: "Видеокарты", 2: "Видеокарты/NVIDIA"}
        result = _get_category_path(2, cat_map)
        assert result == "Видеокарты/NVIDIA"

    def test_category_path_missing(self):
        result = _get_category_path(999, {})
        assert result == ""

    def test_build_category_map(self):
        session = MagicMock()

        cat1 = MagicMock()
        cat1.id = 1
        cat1.name = "Видеокарты"
        cat1.parent_id = None

        cat2 = MagicMock()
        cat2.id = 2
        cat2.name = "NVIDIA"
        cat2.parent_id = 1

        session.query.return_value.all.return_value = [cat1, cat2]

        result = _build_category_map(session)
        assert result[1] == "Видеокарты"
        assert result[2] == "Видеокарты/NVIDIA"

    @patch('sigmaprice.core.database.get_session')
    @patch('sigmaprice.auth.permissions.get_allowed_categories')
    @patch('sigmaprice.auth.permissions.get_allowed_suppliers')
    def test_build_export_data_filters_by_price(
        self, mock_allowed_supp, mock_allowed_cat, mock_get_session
    ):
        session = MagicMock()
        mock_get_session.return_value = session
        mock_allowed_cat.return_value = None
        mock_allowed_supp.return_value = None

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.code = "12345678"
        mock_item.name = "Test Item"
        mock_item.manufacturer = "MSI"
        mock_item.description = "Description"
        mock_item.our_price = Decimal("50000")
        mock_item.rrp = Decimal("55000")
        mock_item.warranty_months = 36
        mock_item.article = "ART-001"
        mock_item.ean = "1234567890123"
        mock_item.category_id = 1

        q5 = MagicMock()
        q5.all.return_value = [mock_item]

        q4 = MagicMock()
        q4.order_by.return_value = q5

        q3 = MagicMock()
        q3.filter.return_value = q4

        q2 = MagicMock()
        q2.filter.return_value = q3

        q1 = MagicMock()
        q1.join.return_value = q2

        session.query.return_value = q1

        cat_map = {1: "Видеокарты"}
        with patch('sigmaprice.export.builder._build_category_map', return_value=cat_map):
            with patch('sigmaprice.export.builder._get_export_suppliers', return_value=[1]):
                with patch('sigmaprice.export.builder._build_supplier_headers', return_value=["П1 (цена)", "П1 (наличие)"]):
                    si = MagicMock()
                    si.price_calculated = Decimal("48000")
                    si.availability = MagicMock()
                    si.availability.value = "in_stock"
                    with patch('sigmaprice.export.builder._get_supplier_item', return_value=si):
                        rows, headers = build_export_data(
                            user_id=1,
                            max_suppliers=10,
                            session=session,
                        )

        assert len(rows) == 1
        assert rows[0]["code"] == "12345678"
        assert rows[0]["our_price"] == Decimal("50000")
        assert rows[0]["supplier_1_price"] == Decimal("48000")
        assert rows[0]["supplier_1_available"] == "in_stock"
        assert len(headers) == 2


class TestExcelWriter:
    """Test Excel file writing."""

    def test_write_excel_creates_file(self, tmp_path):
        filepath = tmp_path / "test.xlsx"
        rows = [
            {
                "category": "Видеокарты",
                "manufacturer": "MSI",
                "reserve1": "",
                "reserve2": "",
                "code": "12345678",
                "name": "Test Item",
                "description": "Desc",
                "our_price": Decimal("50000"),
                "rrp": Decimal("55000"),
                "warranty_months": 36,
                "article": "ART-001",
                "ean": "1234567890123",
                "supplier_1_price": Decimal("48000"),
                "supplier_1_available": "in_stock",
            }
        ]
        supplier_headers = ["П1 (цена)", "П1 (наличие)"]

        result = write_excel(rows, supplier_headers, filepath)
        assert result == filepath
        assert filepath.exists()
        assert filepath.stat().st_size > 0

    def test_write_excel_empty_data(self, tmp_path):
        filepath = tmp_path / "empty.xlsx"
        write_excel([], [], filepath)
        assert filepath.exists()


class TestCSVWriter:
    """Test CSV file writing."""

    def test_write_csv_creates_file(self, tmp_path):
        filepath = tmp_path / "test.csv"
        rows = [
            {
                "category": "Видеокарты",
                "manufacturer": "MSI",
                "reserve1": "",
                "reserve2": "",
                "code": "12345678",
                "name": "Test Item",
                "description": "Desc",
                "our_price": Decimal("50000.00"),
                "rrp": Decimal("55000.00"),
                "warranty_months": 36,
                "article": "ART-001",
                "ean": "1234567890123",
                "supplier_1_price": Decimal("48000.00"),
                "supplier_1_available": "in_stock",
            }
        ]
        supplier_headers = ["П1 (цена)", "П1 (наличие)"]

        result = write_csv(rows, supplier_headers, filepath)
        assert result == filepath
        assert filepath.exists()

        content = filepath.read_text(encoding="utf-8-sig")
        assert "Наша цена" in content
        assert "50000,00" in content
        assert ";" in content

    def test_write_csv_uses_semicolon(self, tmp_path):
        filepath = tmp_path / "delimiter.csv"
        write_csv([], ["П1 (цена)"], filepath)
        content = filepath.read_text(encoding="utf-8-sig")
        assert ";" in content

    def test_write_csv_utf8_bom(self, tmp_path):
        filepath = tmp_path / "bom.csv"
        write_csv([], [], filepath)
        raw = filepath.read_bytes()
        assert raw[:3] == b'\xef\xbb\xbf'
