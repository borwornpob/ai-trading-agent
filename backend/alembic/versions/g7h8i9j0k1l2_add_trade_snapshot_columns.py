"""add trade_reason, pre_trade_snapshot, post_trade_analysis to trades

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-04-13 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('trades', sa.Column('trade_reason', sa.String(255), nullable=True))
    op.add_column('trades', sa.Column('pre_trade_snapshot', sa.JSON(), nullable=True))
    op.add_column('trades', sa.Column('post_trade_analysis', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('trades', 'post_trade_analysis')
    op.drop_column('trades', 'pre_trade_snapshot')
    op.drop_column('trades', 'trade_reason')
