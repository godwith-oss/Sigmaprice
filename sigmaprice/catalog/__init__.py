"""Catalog module — item and category management"""
from sigmaprice.catalog.manager import (
    create_item,
    get_item,
    get_item_by_code,
    get_item_by_article,
    update_item,
    delete_item,
    list_items,
)
from sigmaprice.catalog.code_generator import generate_code
from sigmaprice.catalog.name_builder import build_name
from sigmaprice.catalog.validators import (
    determine_delivery_type,
    is_excluded_delivery,
    validate_name,
    validate_ean,
)
from sigmaprice.catalog.categories import (
    create_category,
    get_category,
    get_category_by_name,
    get_category_tree,
    update_category,
    delete_category,
    list_categories,
    determine_category,
    ensure_default_categories,
)

__all__ = [
    "create_item",
    "get_item",
    "get_item_by_code",
    "get_item_by_article",
    "update_item",
    "delete_item",
    "list_items",
    "generate_code",
    "build_name",
    "determine_delivery_type",
    "is_excluded_delivery",
    "validate_name",
    "validate_ean",
    "create_category",
    "get_category",
    "get_category_by_name",
    "get_category_tree",
    "update_category",
    "delete_category",
    "list_categories",
    "determine_category",
    "ensure_default_categories",
]
