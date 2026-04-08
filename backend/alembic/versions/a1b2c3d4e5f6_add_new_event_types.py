"""add new event types

Revision ID: a1b2c3d4e5f6
Revises: fdeab66c9008
Create Date: 2026-04-08 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fdeab66c9008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE boteventtype ADD VALUE IF NOT EXISTS 'SIGNAL_DETECTED'")
    op.execute("ALTER TYPE boteventtype ADD VALUE IF NOT EXISTS 'TRADE_BLOCKED'")
    op.execute("ALTER TYPE boteventtype ADD VALUE IF NOT EXISTS 'ORDER_FAILED'")


def downgrade() -> None:
    pass
