"""Common data types"""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional
from datetime import datetime


class AvailabilityStatus(str, Enum):
    IN_STOCK = "in_stock"
    RESERVED = "reserved"
    ON_ORDER = "on_order"
    IN_TRANSIT = "in_transit"
    UNAVAILABLE = "unavailable"


class UserRole(str, Enum):
    ADMIN = "admin"
    TRUSTED_USER = "trusted_user"
    USER = "user"


class FeedbackStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class RuleType(str, Enum):
    EXCLUDE_SHEET = "exclude_sheet"
    EXCLUDE_CATEGORY = "exclude_category"
    EXCLUDE_KEYWORD = "exclude_keyword"
    PRICE_RANGE = "price_range"


class KnowledgeBaseRuleType(str, Enum):
    SUFFIX = "suffix"
    SYNONYM = "synonym"
    EXCLUSION = "exclusion"


class KnowledgeBaseSource(str, Enum):
    AI = "ai"
    ADMIN = "admin"
    USER = "user"


@dataclass
class RawItem:
    """Item from supplier price file after parsing"""
    supplier_id: int
    supplier_code: str
    name: str
    description: Optional[str]
    price: Decimal
    currency: str
    availability: AvailabilityStatus
    quantity: Optional[int]
    warranty_months: Optional[int]
    article: Optional[str]
    ean: Optional[str]
    manufacturer: Optional[str]
    delivery_type: Optional[str]


@dataclass
class MatchResult:
    """Result of item matching"""
    catalog_item_id: Optional[int]
    confidence: float
    requires_manual_review: bool


@dataclass
class CatalogItem:
    """Internal catalog item"""
    code: str
    name: str
    description: Optional[str]
    our_price: Optional[Decimal]
    rrp: Optional[Decimal]
    warranty_months: Optional[int]
    manufacturer: Optional[str]
    article: Optional[str]
    ean: Optional[str]
    category_id: Optional[int]
    product_url: Optional[str]
    country_origin: Optional[str]


@dataclass
class PriceResult:
    """Price calculation result"""
    our_price: Decimal
    source_supplier_id: int
    source_status: AvailabilityStatus
    all_suppliers_price: list[tuple[int, Decimal, AvailabilityStatus]]