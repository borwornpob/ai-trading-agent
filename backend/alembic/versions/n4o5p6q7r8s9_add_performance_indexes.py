"""add performance indexes on trades, bot_events, news_sentiments

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-04-15 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "n4o5p6q7r8s9"
down_revision: str | None = "m3n4o5p6q7r8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_trades_open_time", "trades", ["open_time"])
    op.create_index("ix_trades_close_time", "trades", ["close_time"])
    op.create_index("ix_trades_symbol_open_time", "trades", ["symbol", "open_time"])
    op.create_index("ix_bot_events_created_at", "bot_events", ["created_at"])
    op.create_index("ix_news_sentiments_created_at", "news_sentiments", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_news_sentiments_created_at", "news_sentiments")
    op.drop_index("ix_bot_events_created_at", "bot_events")
    op.drop_index("ix_trades_symbol_open_time", "trades")
    op.drop_index("ix_trades_close_time", "trades")
    op.drop_index("ix_trades_open_time", "trades")
