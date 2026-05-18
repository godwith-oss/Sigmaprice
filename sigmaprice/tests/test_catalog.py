"""Tests for Module 5 - Catalog Management"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sigmaprice.catalog import (
    create_item,
    get_item,
    get_item_by_code,
    get_item_by_article,
    update_item,
    delete_item,
    list_items,
    generate_code,
    build_name,
    determine_delivery_type,
    is_excluded_delivery,
    validate_name,
    validate_ean,
    create_category,
    get_category_tree,
    update_category,
    delete_category,
    determine_category,
)
from sigmaprice.core.types import (
    RawItem,
    MatchResult,
    AvailabilityStatus,
)
from sigmaprice.core.exceptions import ValidationError


class TestCodeGenerator:
    """Test unique code generation."""

    def test_generates_8_digit_code(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None

        code = generate_code(session)

        assert len(code) == 8
        assert code.isdigit()
        assert code[0] != '0'

    def test_codes_are_different(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None

        codes = {generate_code(session) for _ in range(50)}

        assert len(codes) == 50

    def test_retry_on_collision_then_success(self):
        session = MagicMock()
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                return MagicMock()
            return None

        session.query.return_value.filter.return_value.first.side_effect = side_effect

        code = generate_code(session)

        assert len(code) == 8
        assert call_count[0] >= 2

    def test_raises_after_max_retries(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = MagicMock()

        with pytest.raises(RuntimeError):
            generate_code(session)


class TestValidators:
    """Test field validators."""

    def test_validate_name_normal(self):
        assert validate_name("RTX 5070") == "RTX 5070"

    def test_validate_name_strips_whitespace(self):
        assert validate_name("  RTX 5070  ") == "RTX 5070"

    def test_validate_name_normalizes_spaces(self):
        assert validate_name("RTX   5070") == "RTX 5070"

    def test_validate_name_empty_raises(self):
        with pytest.raises(ValidationError):
            validate_name("")

    def test_validate_name_none_raises(self):
        with pytest.raises(ValidationError):
            validate_name(None)

    def test_validate_name_too_short_raises(self):
        with pytest.raises(ValidationError):
            validate_name("RT")

    def test_validate_ean_valid(self):
        assert validate_ean("1234567890123") == "1234567890123"

    def test_validate_ean_short_raises(self):
        with pytest.raises(ValidationError):
            validate_ean("12345")

    def test_validate_ean_none_returns_none(self):
        assert validate_ean(None) is None

    def test_validate_ean_empty_returns_none(self):
        assert validate_ean("") is None


class TestDeliveryType:
    """Test delivery type determination."""

    def test_oem_from_tag(self):
        result = determine_delivery_type("RTX 5070", "OEM")
        assert result == "OEM"

    def test_tray_is_oem(self):
        result = determine_delivery_type("Ryzen 7", "TRAY")
        assert result == "OEM"

    def test_box_from_tag(self):
        result = determine_delivery_type("RTX 5070", "BOX")
        assert result == "Retail"

    def test_rtl_from_tag(self):
        result = determine_delivery_type("Intel i5", "RTL")
        assert result == "Retail"

    def test_oem_from_name(self):
        result = determine_delivery_type("Видеокарта RTX 5070 OEM", None)
        assert result == "OEM"

    def test_retail_from_name(self):
        result = determine_delivery_type("Процессор Ryzen 7 BOX", None)
        assert result == "Retail"

    def test_unknown_returns_none(self):
        result = determine_delivery_type("Какой-то товар", None)
        assert result is None

    def test_damaged_packaging_excluded(self):
        assert is_excluded_delivery("Видеокарта, поврежденная упаковка") is True

    def test_damaged_box_excluded(self):
        assert is_excluded_delivery("SSD damaged box") is True

    def test_normal_item_not_excluded(self):
        assert is_excluded_delivery("Видеокарта RTX 5070") is False


class TestNameBuilder:
    """Test name building for different categories."""

    def make_item(self, name="RTX 5070", manufacturer="MSI", description=""):
        return RawItem(
            supplier_id=1,
            supplier_code="VGA-001",
            name=name,
            description=description,
            price=Decimal("50000"),
            currency="RUB",
            availability=AvailabilityStatus.IN_STOCK,
            quantity=10,
            warranty_months=36,
            article="ART-001",
            ean="1234567890123",
            manufacturer=manufacturer,
            delivery_type=None,
        )

    def test_build_video_card_name(self):
        item = self.make_item(
            name="MSI RTX 5070 12Gb GDDR7 SHADOW 2X OC",
            manufacturer="MSI",
        )
        result = build_name(item, "Видеокарты")
        assert "Видеокарта" in result
        assert "MSI" in result
        assert "RTX 5070" in result

    def test_build_motherboard_name(self):
        item = self.make_item(
            name="Gigabyte B860M D3HP",
            manufacturer="Gigabyte",
            description="LGA1851",
        )
        result = build_name(item, "Материнские платы")
        assert "Материнская плата" in result
        assert "Gigabyte" in result
        assert "LGA1851" in result

    def test_build_processor_name(self):
        item = self.make_item(
            name="AMD Ryzen 7 7800X3D",
            manufacturer="AMD",
            description="AM5",
        )
        result = build_name(item, "Процессоры")
        assert "Процессор" in result
        assert "Ryzen" in result
        assert "AM5" in result

    def test_build_ssd_name(self):
        item = self.make_item(
            name="Samsung 990 Pro",
            manufacturer="Samsung",
            description="2TB NVMe",
        )
        result = build_name(item, "SSD")
        assert "SSD" in result
        assert "Samsung" in result

    def test_build_generic_name(self):
        item = self.make_item(
            name="Какой-то товар",
            manufacturer="SomeBrand",
        )
        result = build_name(item, "Прочее")
        assert "SomeBrand" in result

    def test_build_name_handles_missing_manufacturer(self):
        item = self.make_item(name="Generic Item", manufacturer=None)
        result = build_name(item, "Прочее")
        assert "Generic Item" in result


class TestCategories:
    """Test category management."""

    @patch('sigmaprice.core.database.get_session')
    def test_create_category(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        cat = MagicMock()
        cat.id = 1
        cat.name = "Видеокарты"
        session.add.return_value = None
        session.commit.return_value = None
        session.refresh.return_value = None

        with patch('sigmaprice.catalog.categories.Category', return_value=cat):
            result = create_category("Видеокарты", session=session)
            assert result.name == "Видеокарты"
            assert session.add.called

    def test_create_category_empty_name_raises(self):
        with pytest.raises(ValidationError):
            create_category("   ", session=MagicMock())

    @patch('sigmaprice.core.database.get_session')
    def test_get_category_tree_returns_nested(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        cat1 = MagicMock()
        cat1.id = 1
        cat1.name = "Видеокарты"
        cat1.parent_id = None
        cat1.sort_field = "price"

        cat2 = MagicMock()
        cat2.id = 2
        cat2.name = "NVIDIA"
        cat2.parent_id = 1
        cat2.sort_field = "price"

        cat3 = MagicMock()
        cat3.id = 3
        cat3.name = "AMD"
        cat3.parent_id = 1
        cat3.sort_field = "price"

        cat4 = MagicMock()
        cat4.id = 4
        cat4.name = "Процессоры"
        cat4.parent_id = None
        cat4.sort_field = "price"

        session.query.return_value.order_by.return_value.all.return_value = [
            cat1, cat2, cat3, cat4
        ]

        tree = get_category_tree(session=session)
        assert len(tree) == 2
        assert tree[0]["name"] == "Видеокарты"
        assert len(tree[0]["children"]) == 2

    @patch('sigmaprice.core.database.get_session')
    def test_delete_category_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        result = delete_category(999, session=session)
        assert result is False

    def test_determine_category_by_keyword(self):
        session = MagicMock()

        cat = MagicMock()
        cat.id = 5
        cat.name = "Видеокарты"
        session.query.return_value.filter.return_value.first.return_value = cat

        item = RawItem(
            supplier_id=1,
            supplier_code="VGA-001",
            name="Видеокарта MSI RTX 5070",
            description="",
            price=Decimal("50000"),
            currency="RUB",
            availability=AvailabilityStatus.IN_STOCK,
            quantity=None,
            warranty_months=None,
            article=None,
            ean=None,
            manufacturer="MSI",
            delivery_type=None,
        )

        result = determine_category(item, session=session)
        assert result == 5


class TestManager:
    """Test catalog item CRUD operations."""

    def make_raw_item(self, **kwargs):
        defaults = {
            "supplier_id": 1,
            "supplier_code": "VGA-001",
            "name": "MSI RTX 5070 12Gb",
            "description": "Gaming video card",
            "price": Decimal("55000"),
            "currency": "RUB",
            "availability": AvailabilityStatus.IN_STOCK,
            "quantity": 5,
            "warranty_months": 36,
            "article": "RTX5070-MSI",
            "ean": "1234567890123",
            "manufacturer": "MSI",
            "delivery_type": None,
        }
        defaults.update(kwargs)
        return RawItem(**defaults)

    def make_match_result(self, **kwargs):
        defaults = {
            "catalog_item_id": None,
            "confidence": 0.95,
            "requires_manual_review": False,
        }
        defaults.update(kwargs)
        return MatchResult(**defaults)

    @patch('sigmaprice.core.database.get_session')
    @patch('sigmaprice.catalog.manager.generate_code')
    @patch('sigmaprice.catalog.manager.determine_category')
    def test_create_item_success(
        self, mock_determine_cat, mock_gen_code, mock_get_session
    ):
        session = MagicMock()
        mock_get_session.return_value = session
        mock_gen_code.return_value = "13784256"
        mock_determine_cat.return_value = 5

        category = MagicMock()
        category.name = "Видеокарты"
        session.query.return_value.filter.return_value.first.return_value = category

        item = self.make_raw_item()
        match_result = self.make_match_result()

        with patch('sigmaprice.catalog.manager.CatalogItemModel') as mock_model:
            catalog_item = MagicMock()
            catalog_item.id = 1
            catalog_item.code = "13784256"
            catalog_item.name = "Видеокарта MSI RTX 5070 12Gb"
            mock_model.return_value = catalog_item

            with patch('sigmaprice.db.models.SupplierItemMapping') as mock_mapping:
                result = create_item(item, match_result, session=session)

        assert result.code == "13784256"
        assert session.add.called
        assert session.commit.called

    @patch('sigmaprice.core.database.get_session')
    def test_get_item_by_code_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_item = MagicMock()
        mock_item.code = "13784256"
        session.query.return_value.filter.return_value.first.return_value = mock_item

        result = get_item_by_code("13784256", session=session)
        assert result is not None
        assert result.code == "13784256"

    @patch('sigmaprice.core.database.get_session')
    def test_get_item_by_code_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        result = get_item_by_code("99999999", session=session)
        assert result is None

    @patch('sigmaprice.core.database.get_session')
    def test_get_item_by_article(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_item = MagicMock()
        mock_item.article = "RTX5070-MSI"
        session.query.return_value.filter.return_value.first.return_value = mock_item

        result = get_item_by_article("RTX5070-MSI", session=session)
        assert result is not None
        assert result.article == "RTX5070-MSI"

    @patch('sigmaprice.core.database.get_session')
    def test_update_item_forbidden_code_raises(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_item = MagicMock()
        mock_item.id = 1
        session.query.return_value.filter.return_value.first.return_value = mock_item

        with pytest.raises(ValidationError, match="cannot be updated"):
            update_item(1, code="99999999", session=session)

    @patch('sigmaprice.core.database.get_session')
    def test_update_item_success(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.code = "13784256"
        mock_item.name = "Old Name"
        session.query.return_value.filter.return_value.first.return_value = mock_item

        result = update_item(1, name="New Name", manufacturer="MSI", session=session)

        assert mock_item.name == "New Name"
        assert mock_item.manufacturer == "MSI"
        assert session.commit.called

    @patch('sigmaprice.core.database.get_session')
    def test_update_item_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValidationError, match="not found"):
            update_item(999, name="Test", session=session)

    @patch('sigmaprice.core.database.get_session')
    def test_delete_item_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        result = delete_item(999, session=session)
        assert result is False

    @patch('sigmaprice.core.database.get_session')
    def test_delete_item_success(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.code = "13784256"
        session.query.return_value.filter.return_value.first.return_value = mock_item
        session.query.return_value.filter.return_value.update.return_value = None

        result = delete_item(1, session=session)
        assert result is True
        assert session.delete.called

    @patch('sigmaprice.core.database.get_session')
    def test_list_items_with_filters(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_item = MagicMock()
        ordered_query = MagicMock()
        ordered_query.all.return_value = [mock_item]
        session.query.return_value.filter.return_value.filter.return_value.order_by.return_value = ordered_query

        result = list_items(
            filters={"category_id": 5, "manufacturer": "MSI"},
            session=session,
        )
        assert len(result) == 1

    @patch('sigmaprice.core.database.get_session')
    @patch('sigmaprice.catalog.manager.generate_code')
    @patch('sigmaprice.catalog.manager.determine_category')
    def test_create_item_excluded_delivery(
        self, mock_determine_cat, mock_gen_code, mock_get_session
    ):
        session = MagicMock()
        mock_get_session.return_value = session
        mock_gen_code.return_value = "13784256"
        mock_determine_cat.return_value = 5

        item = self.make_raw_item(
            name="Видеокарта поврежденная упаковка RTX 5070"
        )
        match_result = self.make_match_result()

        with pytest.raises(ValidationError, match="damaged"):
            create_item(item, match_result, session=session)

    @patch('sigmaprice.core.database.get_session')
    def test_get_item_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.code = "13784256"
        session.query.return_value.filter.return_value.first.return_value = mock_item

        result = get_item(1, session=session)
        assert result is not None
        assert result.id == 1
