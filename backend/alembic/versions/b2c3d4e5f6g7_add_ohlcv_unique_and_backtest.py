"""add ohlcv unique constraint and backtest_result column

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-08 22:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint on ohlcv_data for upsert support
    op.create_unique_constraint(
        'uq_ohlcv_symbol_timeframe_time',
        'ohlcv_data',
        ['symbol', 'timeframe', 'time']
    )
    # Add backtest_result column to ai_optimization_logs
    op.add_column(
        'ai_optimization_logs',
        sa.Column('backtest_result', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('ai_optimization_logs', 'backtest_result')
    op.drop_constraint('uq_ohlcv_symbol_timeframe_time', 'ohlcv_data', type_='unique')
