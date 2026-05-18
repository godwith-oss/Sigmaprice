"""Add display_name, is_active, created_by to users table

Revision ID: 004
Revises: 003
Create Date: 2026-05-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users',
        sa.Column('display_name', sa.String(length=200), nullable=True)
    )
    op.add_column('users',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
    )
    op.add_column('users',
        sa.Column('created_by', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_users_created_by',
        'users', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_users_created_by', 'users', type_='foreignkey')
    op.drop_column('users', 'created_by')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'display_name')
