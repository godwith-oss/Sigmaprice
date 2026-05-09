"""Initial schema - create all tables

Revision ID: 001
Revises:
Create Date: 2026-05-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table('suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('vat_included', sa.Boolean(), nullable=True),
        sa.Column('price_formula', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_suppliers_name', 'suppliers', ['name'])

    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('sort_field', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_categories_parent', 'categories', ['parent_id'])
    op.create_index('idx_categories_name', 'categories', ['name'])

    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=200), nullable=False),
        sa.Column('role', sa.Enum('admin', 'trusted_user', 'user', name='user_role'), nullable=False),
        sa.Column('is_trusted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_username', 'users', ['username'])

    op.create_table('catalog_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=8), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('our_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('rrp', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('warranty_months', sa.Integer(), nullable=True),
        sa.Column('manufacturer', sa.String(length=200), nullable=True),
        sa.Column('article', sa.String(length=100), nullable=True),
        sa.Column('ean', sa.String(length=20), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('product_url', sa.String(length=500), nullable=True),
        sa.Column('country_origin', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_catalog_items_code', 'catalog_items', ['code'])
    op.create_index('idx_catalog_items_article', 'catalog_items', ['article'])
    op.create_index('idx_catalog_items_ean', 'catalog_items', ['ean'])
    op.create_index('idx_catalog_items_category', 'catalog_items', ['category_id'])
    op.create_index('idx_catalog_items_name', 'catalog_items', ['name'])

    op.create_table('supplier_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('rule_type', sa.Enum('exclude_sheet', 'exclude_category', 'exclude_keyword', 'price_range', name='rule_type'), nullable=False),
        sa.Column('rule_value', sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_supplier_rules_supplier', 'supplier_rules', ['supplier_id'])

    op.create_table('supplier_column_map',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('our_field', sa.String(length=50), nullable=False),
        sa.Column('supplier_column', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_supplier_column_map_supplier', 'supplier_column_map', ['supplier_id'])

    op.create_table('supplier_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('supplier_code', sa.String(length=100), nullable=False),
        sa.Column('catalog_item_id', sa.Integer(), nullable=True),
        sa.Column('price_original', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('price_calculated', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('availability', sa.Enum('in_stock', 'reserved', 'on_order', 'in_transit', 'unavailable', name='availability_status'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('warranty_months', sa.Integer(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['catalog_item_id'], ['catalog_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_supplier_items_supplier_code', 'supplier_items', ['supplier_code'])
    op.create_index('idx_supplier_items_catalog_item', 'supplier_items', ['catalog_item_id'])
    op.create_index('idx_supplier_items_supplier', 'supplier_items', ['supplier_id'])

    op.create_table('supplier_item_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('catalog_item_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('supplier_code', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['catalog_item_id'], ['catalog_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('catalog_item_id', 'supplier_id', 'supplier_code')
    )
    op.create_index('idx_supplier_item_mapping_lookup', 'supplier_item_mapping', ['supplier_id', 'supplier_code'])

    op.create_table('price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_item_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('availability', sa.Enum('in_stock', 'reserved', 'on_order', 'in_transit', 'unavailable', name='availability_status'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.Column('upload_number', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['supplier_item_id'], ['supplier_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_price_history_supplier_upload', 'price_history', ['supplier_item_id', 'upload_number'])
    op.create_index('idx_price_history_recorded', 'price_history', ['recorded_at'])

    op.create_table('item_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('catalog_item_id', sa.Integer(), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['catalog_item_id'], ['catalog_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('catalog_item_id')
    )
    op.create_index('idx_item_embeddings_catalog', 'item_embeddings', ['catalog_item_id'])

    op.create_table('user_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_permissions_user', 'user_permissions', ['user_id'])
    op.create_index('idx_user_permissions_category', 'user_permissions', ['category_id'])
    op.create_index('idx_user_permissions_supplier', 'user_permissions', ['supplier_id'])

    op.create_table('feedback_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('catalog_item_id', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'resolved', 'rejected', name='feedback_status'), nullable=True),
        sa.Column('ai_resolution', sa.Text(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['catalog_item_id'], ['catalog_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_feedback_items_status', 'feedback_items', ['status'])
    op.create_index('idx_feedback_items_user', 'feedback_items', ['user_id'])
    op.create_index('idx_feedback_items_catalog', 'feedback_items', ['catalog_item_id'])

    op.create_table('knowledge_base',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_type', sa.Enum('suffix', 'synonym', 'exclusion', name='knowledge_base_rule_type'), nullable=False),
        sa.Column('pattern', sa.String(length=200), nullable=False),
        sa.Column('resolution', sa.String(length=500), nullable=False),
        sa.Column('source', sa.Enum('ai', 'admin', 'user', name='knowledge_base_source'), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_knowledge_base_pattern', 'knowledge_base', ['pattern'])
    op.create_index('idx_knowledge_base_rule_type', 'knowledge_base', ['rule_type'])


def downgrade() -> None:
    op.drop_table('knowledge_base')
    op.drop_table('feedback_items')
    op.drop_table('user_permissions')
    op.drop_table('item_embeddings')
    op.drop_table('price_history')
    op.drop_table('supplier_item_mapping')
    op.drop_table('supplier_items')
    op.drop_table('supplier_column_map')
    op.drop_table('supplier_rules')
    op.drop_table('catalog_items')
    op.drop_table('users')
    op.drop_table('categories')
    op.drop_table('suppliers')

    op.execute('DROP TYPE IF EXISTS knowledge_base_source')
    op.execute('DROP TYPE IF EXISTS knowledge_base_rule_type')
    op.execute('DROP TYPE IF EXISTS feedback_status')
    op.execute('DROP TYPE IF EXISTS user_role')
    op.execute('DROP TYPE IF EXISTS availability_status')
    op.execute('DROP TYPE IF EXISTS rule_type')
    op.execute('DROP EXTENSION IF EXISTS vector')