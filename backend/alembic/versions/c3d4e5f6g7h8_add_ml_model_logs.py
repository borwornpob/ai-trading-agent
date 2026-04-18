"""add ml_model_logs table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-04-08 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ml_model_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        sa.Column('train_start', sa.DateTime(), nullable=False),
        sa.Column('train_end', sa.DateTime(), nullable=False),
        sa.Column('test_start', sa.DateTime(), nullable=False),
        sa.Column('test_end', sa.DateTime(), nullable=False),
        sa.Column('metrics', sa.Text(), nullable=True),
        sa.Column('feature_importance', sa.Text(), nullable=True),
        sa.Column('model_path', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('ml_model_logs')
