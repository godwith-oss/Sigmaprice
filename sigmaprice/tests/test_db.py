"""Tests for Module 1 - Database"""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sigmaprice.db.models import (
    Base, Supplier, SupplierRule, SupplierColumnMap, Category,
    CatalogItem, SupplierItem, SupplierItemMapping, PriceHistory,
    ItemEmbedding, User, UserPermission, FeedbackItem, KnowledgeBase,
    AvailabilityStatus, UserRole, FeedbackStatus
)


TEST_DATABASE_URL = "postgresql://sigmaprice:password@localhost:5432/sigmaprice_test"


@pytest.fixture
def engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    """Create database session"""
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def tables(engine):
    """Get list of tables"""
    inspector = inspect(engine)
    return inspector.get_table_names()


def test_all_tables_exist(tables):
    """Verify all 13 tables are created"""
    expected_tables = [
        'suppliers', 'supplier_rules', 'supplier_column_map',
        'categories', 'catalog_items', 'supplier_items',
        'supplier_item_mapping', 'price_history', 'item_embeddings',
        'users', 'user_permissions', 'feedback_items', 'knowledge_base'
    ]
    for table in expected_tables:
        assert table in tables, f"Table {table} not found"


def test_supplier_model(session):
    """Test Supplier model creation"""
    supplier = Supplier(
        name="Test Supplier",
        country="Russia",
        currency="RUB",
        vat_included=True,
        price_formula="price * 1.2"
    )
    session.add(supplier)
    session.commit()

    result = session.query(Supplier).first()
    assert result.name == "Test Supplier"
    assert result.country == "Russia"
    assert result.currency == "RUB"


def test_category_model(session):
    """Test Category model creation"""
    parent = Category(name="Electronics", sort_field="price")
    session.add(parent)
    session.commit()

    child = Category(name="GPU", parent_id=parent.id, sort_field="price")
    session.add(child)
    session.commit()

    result = session.query(Category).filter_by(name="GPU").first()
    assert result.parent_id == parent.id


def test_catalog_item_model(session):
    """Test CatalogItem model creation"""
    item = CatalogItem(
        code="12345678",
        name="NVIDIA RTX 5080",
        description="Graphics card",
        our_price=999.99,
        rrp=1199.99,
        warranty_months=36,
        manufacturer="NVIDIA",
        article="RTX5080"
    )
    session.add(item)
    session.commit()

    result = session.query(CatalogItem).first()
    assert result.code == "12345678"
    assert result.name == "NVIDIA RTX 5080"


def test_supplier_item_model(session):
    """Test SupplierItem model creation"""
    supplier = Supplier(name="Test", country="Test", currency="USD")
    session.add(supplier)
    session.commit()

    item = SupplierItem(
        supplier_id=supplier.id,
        supplier_code="SKU001",
        price_original=100.00,
        price_calculated=120.00,
        availability=AvailabilityStatus.IN_STOCK
    )
    session.add(item)
    session.commit()

    result = session.query(SupplierItem).first()
    assert result.availability == AvailabilityStatus.IN_STOCK


def test_user_model(session):
    """Test User model creation"""
    user = User(
        username="admin",
        password_hash="$2b$12$hash",
        role=UserRole.ADMIN,
        is_trusted=True
    )
    session.add(user)
    session.commit()

    result = session.query(User).first()
    assert result.username == "admin"
    assert result.role == UserRole.ADMIN


def test_foreign_keys_work(session):
    """Test foreign key relationships"""
    supplier = Supplier(name="Supplier", country="C", currency="RUB")
    session.add(supplier)
    session.commit()

    rule = SupplierRule(
        supplier_id=supplier.id,
        rule_type="exclude_keyword",
        rule_value="test"
    )
    session.add(rule)
    session.commit()

    result = session.query(SupplierRule).first()
    assert result.supplier.name == "Supplier"


def test_enum_values(session):
    """Test enum values are stored correctly"""
    item = SupplierItem(
        supplier_id=1,
        supplier_code="test",
        price_original=100,
        price_calculated=100,
        availability=AvailabilityStatus.ON_ORDER
    )
    session.add(item)
    session.commit()

    result = session.query(SupplierItem).first()
    assert result.availability == AvailabilityStatus.ON_ORDER
    assert result.availability.value == "on_order"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])