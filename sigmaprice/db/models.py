"""SQLAlchemy models for all database tables"""
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Boolean, Enum,
    ForeignKey, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class AvailabilityStatus(enum.Enum):
    IN_STOCK = "in_stock"
    RESERVED = "reserved"
    ON_ORDER = "on_order"
    IN_TRANSIT = "in_transit"
    UNAVAILABLE = "unavailable"


class UserRole(enum.Enum):
    ADMIN = "admin"
    TRUSTED_USER = "trusted_user"
    USER = "user"


class FeedbackStatus(enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    AUTO_RESOLVED = "auto_resolved"
    MANUAL_REQUIRED = "manual_required"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class RuleType(enum.Enum):
    EXCLUDE_SHEET = "exclude_sheet"
    EXCLUDE_CATEGORY = "exclude_category"
    EXCLUDE_KEYWORD = "exclude_keyword"
    PRICE_RANGE = "price_range"


class KnowledgeBaseRuleType(enum.Enum):
    SUFFIX = "suffix"
    SYNONYM = "synonym"
    EXCLUSION = "exclusion"


class KnowledgeBaseSource(enum.Enum):
    AI = "ai"
    ADMIN = "admin"
    USER = "user"


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    currency = Column(String(3), nullable=False)
    vat_included = Column(Boolean, default=False)
    price_formula = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rules = relationship("SupplierRule", back_populates="supplier", cascade="all, delete-orphan")
    column_maps = relationship("SupplierColumnMap", back_populates="supplier", cascade="all, delete-orphan")
    items = relationship("SupplierItem", back_populates="supplier")
    mappings = relationship("SupplierItemMapping", back_populates="supplier")


class SupplierRule(Base):
    __tablename__ = "supplier_rules"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    rule_type = Column(Enum(RuleType), nullable=False)
    rule_value = Column(String(500), nullable=False)

    supplier = relationship("Supplier", back_populates="rules")


class SupplierColumnMap(Base):
    __tablename__ = "supplier_column_map"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    our_field = Column(String(50), nullable=False)
    supplier_column = Column(String(100), nullable=False)

    supplier = relationship("Supplier", back_populates="column_maps")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    sort_field = Column(String(20), default="price")
    created_at = Column(DateTime, default=datetime.utcnow)

    children = relationship("Category", backref="parent", remote_side=[id])
    catalog_items = relationship("CatalogItem", back_populates="category")


class CatalogItem(Base):
    __tablename__ = "catalog_items"

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, unique=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    our_price = Column(Numeric(12, 2), nullable=True)
    rrp = Column(Numeric(12, 2), nullable=True)
    warranty_months = Column(Integer, nullable=True)
    manufacturer = Column(String(200), nullable=True)
    article = Column(String(100), nullable=True)
    ean = Column(String(20), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    product_url = Column(String(500), nullable=True)
    country_origin = Column(String(100), nullable=True)
    delivery_type = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="catalog_items")
    supplier_items = relationship("SupplierItem", back_populates="catalog_item")
    mappings = relationship("SupplierItemMapping", back_populates="catalog_item")
    embedding = relationship("ItemEmbedding", back_populates="catalog_item", uselist=False)
    feedback_items = relationship("FeedbackItem", back_populates="catalog_item")

    __table_args__ = (
        Index("idx_code", "code"),
        Index("idx_article", "article"),
        Index("idx_ean", "ean"),
        Index("idx_category", "category_id"),
    )


class SupplierItem(Base):
    __tablename__ = "supplier_items"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    supplier_code = Column(String(100), nullable=False)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True)
    price_original = Column(Numeric(12, 2), nullable=False)
    price_calculated = Column(Numeric(12, 2), nullable=False)
    availability = Column(Enum(AvailabilityStatus), nullable=False)
    quantity = Column(Integer, nullable=True)
    warranty_months = Column(Integer, nullable=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="items")
    catalog_item = relationship("CatalogItem", back_populates="supplier_items")
    price_history = relationship("PriceHistory", back_populates="supplier_item", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_supplier_code", "supplier_code"),
        Index("idx_catalog_item", "catalog_item_id"),
    )


class SupplierItemMapping(Base):
    __tablename__ = "supplier_item_mapping"

    id = Column(Integer, primary_key=True)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    supplier_code = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    catalog_item = relationship("CatalogItem", back_populates="mappings")
    supplier = relationship("Supplier", back_populates="mappings")

    __table_args__ = (
        Index("idx_lookup", "supplier_id", "supplier_code"),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    supplier_item_id = Column(Integer, ForeignKey("supplier_items.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    availability = Column(Enum(AvailabilityStatus), nullable=False)
    quantity = Column(Integer, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    upload_number = Column(Integer, nullable=False)

    supplier_item = relationship("SupplierItem", back_populates="price_history")

    __table_args__ = (
        Index("idx_supplier_upload", "supplier_item_id", "upload_number"),
    )


class ItemEmbedding(Base):
    __tablename__ = "item_embeddings"

    id = Column(Integer, primary_key=True)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id", ondelete="CASCADE"), nullable=False, unique=True)
    embedding = Column(Text, nullable=False)
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    catalog_item = relationship("CatalogItem", back_populates="embedding")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_trusted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
    feedback_items = relationship("FeedbackItem", back_populates="user")


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="permissions")


class FeedbackItem(Base):
    __tablename__ = "feedback_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id", ondelete="CASCADE"), nullable=True)
    comment = Column(Text, nullable=False)
    status = Column(Enum(FeedbackStatus), default=FeedbackStatus.PENDING)
    ai_resolution = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    auto_fixed = Column(Boolean, default=False)

    user = relationship("User", back_populates="feedback_items")
    catalog_item = relationship("CatalogItem", back_populates="feedback_items")

    __table_args__ = (
        Index("idx_status", "status"),
    )


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True)
    rule_type = Column(Enum(KnowledgeBaseRuleType), nullable=False)
    pattern = Column(String(200), nullable=False)
    resolution = Column(String(500), nullable=False)
    source = Column(Enum(KnowledgeBaseSource), nullable=False)
    confidence = Column(Numeric(5, 2), default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)