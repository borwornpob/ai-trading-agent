"""add missing event types SETTINGS_CHANGED and STRATEGY_CHANGED

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-04-13 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'k1l2m3n4o5p6'
down_revision: Union[str, None] = 'j0k1l2m3n4o5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE boteventtype ADD VALUE IF NOT EXISTS 'SETTINGS_CHANGED'")
    op.execute("ALTER TYPE boteventtype ADD VALUE IF NOT EXISTS 'STRATEGY_CHANGED'")


def downgrade() -> None:
    pass
