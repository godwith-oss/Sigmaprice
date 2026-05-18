"""Add delivery_type field to catalog_items

Revision ID: 002
Revises: 001
Create Date: 2026-05-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('catalog_items',
        sa.Column('delivery_type', sa.String(length=20), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('catalog_items', 'delivery_type')
