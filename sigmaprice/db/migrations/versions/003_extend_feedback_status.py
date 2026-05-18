"""Extend FeedbackStatus enum and add auto_fixed column

Revision ID: 003
Revises: 002
Create Date: 2026-05-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE feedback_status ADD VALUE IF NOT EXISTS 'analyzing'")
    op.execute("ALTER TYPE feedback_status ADD VALUE IF NOT EXISTS 'auto_resolved'")
    op.execute("ALTER TYPE feedback_status ADD VALUE IF NOT EXISTS 'manual_required'")

    op.add_column('feedback_items',
        sa.Column('auto_fixed', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('feedback_items', 'auto_fixed')
