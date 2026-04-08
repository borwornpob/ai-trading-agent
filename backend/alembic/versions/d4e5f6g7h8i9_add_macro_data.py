"""add macro_data table

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-04-08 23:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'macro_data',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('series_id', sa.String(50), nullable=False),
        sa.Column('series_name', sa.String(200), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_macro_data_series_id', 'macro_data', ['series_id'])
    op.create_index('ix_macro_data_date', 'macro_data', ['date'])
    op.create_unique_constraint('uq_macro_series_date', 'macro_data', ['series_id', 'date'])


def downgrade() -> None:
    op.drop_table('macro_data')
