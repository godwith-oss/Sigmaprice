"""Tests for Module 2 - Suppliers"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sigmaprice.suppliers import (
    create_supplier, get_supplier, update_supplier, delete_supplier,
    add_rule, get_rules, should_exclude,
    calculate_price, validate_formula,
    set_column_mapping, get_column_mapping
)
from sigmaprice.core.types import RawItem, AvailabilityStatus
from sigmaprice.core.exceptions import SupplierError, ValidationError


class TestSupplierManager:
    """Test supplier CRUD operations."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None
        session.query.return_value.filter.return_value.all.return_value = []
        return session

    @patch('sigmaprice.suppliers.manager.get_session')
    def test_create_supplier_valid(self, mock_get_session):
        """Test creating supplier with valid data."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        supplier = MagicMock()
        supplier.id = 1
        supplier.name = "Test Supplier"
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        with patch('sigmaprice.suppliers.manager.Supplier', return_value=supplier):
            result = create_supplier(
                name="Test Supplier",
                country="Russia",
                currency="USD",
                vat_included=False
            )

        assert mock_session.add.called
        assert mock_session.commit.called

    @patch('sigmaprice.suppliers.manager.get_session')
    def test_create_supplier_empty_name(self, mock_get_session):
        """Test creating supplier with empty name."""
        with pytest.raises(ValidationError):
            create_supplier(
                name="",
                country="Russia",
                currency="USD",
                vat_included=False
            )

    @patch('sigmaprice.suppliers.manager.get_session')
    def test_create_supplier_invalid_currency(self, mock_get_session):
        """Test creating supplier with invalid currency."""
        with pytest.raises(ValidationError):
            create_supplier(
                name="Test",
                country="Russia",
                currency="GBP",
                vat_included=False
            )

    @patch('sigmaprice.suppliers.manager.get_session')
    def test_get_supplier_found(self, mock_get_session):
        """Test getting existing supplier."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        supplier = MagicMock()
        supplier.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = supplier

        result = get_supplier(1)
        assert result is not None

    @patch('sigmaprice.suppliers.manager.get_session')
    def test_get_supplier_not_found(self, mock_get_session):
        """Test getting non-existent supplier."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = get_supplier(999)
        assert result is None


class TestRules:
    """Test exclusion rules."""

    @patch('sigmaprice.suppliers.rules.get_session')
    def test_add_rule_valid(self, mock_get_session):
        """Test adding a valid rule."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        supplier = MagicMock()
        supplier.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = supplier

        rule = MagicMock()
        rule.id = 1

        with patch('sigmaprice.suppliers.rules.SupplierRule', return_value=rule):
            result = add_rule(
                supplier_id=1,
                rule_type="exclude_keyword",
                rule_value="demo"
            )

        assert mock_session.add.called

    @patch('sigmaprice.suppliers.rules.get_session')
    def test_add_rule_invalid_type(self, mock_get_session):
        """Test adding rule with invalid type."""
        with pytest.raises(SupplierError):
            add_rule(
                supplier_id=1,
                rule_type="invalid_type",
                rule_value="test"
            )

    @patch('sigmaprice.suppliers.rules.get_session')
    def test_should_exclude_keyword(self, mock_get_session):
        """Test keyword exclusion."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        rule = MagicMock()
        rule.rule_type.value = 'exclude_keyword'
        rule.rule_value = 'demo'

        mock_session.query.return_value.filter.return_value.all.return_value = [rule]

        item = RawItem(
            supplier_id=1,
            supplier_code="SKU001",
            name="Demo product",
            description=None,
            price=Decimal("100"),
            currency="USD",
            availability=AvailabilityStatus.IN_STOCK,
            quantity=10,
            warranty_months=None,
            article=None,
            ean=None,
            manufacturer=None,
            delivery_type=None
        )

        result = should_exclude(1, item)
        assert result is True


class TestPricing:
    """Test price calculation."""

    @patch('sigmaprice.suppliers.pricing.get_session')
    def test_calculate_price_with_formula(self, mock_get_session):
        """Test price calculation with formula."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        supplier = MagicMock()
        supplier.price_formula = "price * 1.2"
        mock_session.query.return_value.filter.return_value.first.return_value = supplier

        result = calculate_price(
            supplier_id=1,
            price_original=Decimal("100.00"),
            session=mock_session
        )

        assert result == Decimal("120.00")

    @patch('sigmaprice.suppliers.pricing.get_session')
    def test_calculate_price_no_formula(self, mock_get_session):
        """Test price calculation without formula."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        supplier = MagicMock()
        supplier.price_formula = None
        mock_session.query.return_value.filter.return_value.first.return_value = supplier

        result = calculate_price(
            supplier_id=1,
            price_original=Decimal("100.00"),
            session=mock_session
        )

        assert result == Decimal("100.00")


class TestColumnMapping:
    """Test column mapping."""

    @patch('sigmaprice.suppliers.column_mapping.get_session')
    def test_set_column_mapping(self, mock_get_session):
        """Test setting column mapping."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        supplier = MagicMock()
        supplier.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = supplier

        result = set_column_mapping(1, {
            'code': 'Код',
            'name': 'Наименование',
            'price': 'Цена',
        })

        assert result is True

    @patch('sigmaprice.suppliers.column_mapping.get_session')
    def test_get_column_mapping(self, mock_get_session):
        """Test getting column mapping."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mapping = MagicMock()
        mapping.our_field = 'code'
        mapping.supplier_column = 'Код'

        mock_session.query.return_value.filter.return_value.all.return_value = [mapping]

        result = get_column_mapping(1)

        assert 'code' in result
        assert result['code'] == 'Код'

    @patch('sigmaprice.suppliers.column_mapping.get_session')
    def test_set_column_mapping_invalid_field(self, mock_get_session):
        """Test setting column mapping with invalid field."""
        with pytest.raises(ValidationError):
            set_column_mapping(1, {
                'invalid_field': 'Some Column'
            })


class TestValidateFormula:
    """Test formula validation."""

    def test_validate_formula_simple(self):
        """Test simple formula validation."""
        assert validate_formula("price") is True
        assert validate_formula("price * 1.2") is True

    def test_validate_formula_invalid(self):
        """Test invalid formula."""
        assert validate_formula("import os") is False
        assert validate_formula("exec('test')") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])