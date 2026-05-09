"""Suppliers module - public interface"""
from sigmaprice.suppliers.manager import (
    create_supplier,
    get_supplier,
    get_supplier_by_name,
    update_supplier,
    delete_supplier,
    list_suppliers
)

from sigmaprice.suppliers.rules import (
    add_rule,
    get_rules,
    delete_rule,
    should_exclude
)

from sigmaprice.suppliers.pricing import (
    calculate_price,
    validate_formula,
    calculate_with_vat
)

from sigmaprice.suppliers.column_mapping import (
    set_column_mapping,
    get_column_mapping,
    clear_column_mapping,
    get_field_by_column
)

__all__ = [
    # Manager
    'create_supplier',
    'get_supplier',
    'get_supplier_by_name',
    'update_supplier',
    'delete_supplier',
    'list_suppliers',
    # Rules
    'add_rule',
    'get_rules',
    'delete_rule',
    'should_exclude',
    # Pricing
    'calculate_price',
    'validate_formula',
    'calculate_with_vat',
    # Column mapping
    'set_column_mapping',
    'get_column_mapping',
    'clear_column_mapping',
    'get_field_by_column',
]