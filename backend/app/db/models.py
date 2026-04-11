import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BotEventType(str, enum.Enum):
    STARTED = "STARTED"
    STOPPED = "STOPPED"
    TRADE_OPENED = "TRADE_OPENED"
    TRADE_CLOSED = "TRADE_CLOSED"
    SIGNAL_DETECTED = "SIGNAL_DETECTED"
    TRADE_BLOCKED = "TRADE_BLOCKED"
    ORDER_FAILED = "ORDER_FAILED"
    ERROR = "ERROR"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    SENTIMENT_CHANGE = "SENTIMENT_CHANGE"
    OPTIMIZATION_RUN = "OPTIMIZATION_RUN"
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    STRATEGY_CHANGED = "STRATEGY_CHANGED"


class OHLCVData(Base):
    __tablename__ = "ohlcv_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    timeframe: Mapped[str] = mapped_column(String(10))
    time: Mapped[datetime] = mapped_column(DateTime, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20))
    type: Mapped[str] = mapped_column(String(10))  # BUY / SELL
    lot: Mapped[float] = mapped_column(Float)
    open_price: Mapped[float] = mapped_column(Float)
    expected_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # tick price before order, for slippage calc
    close_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sl: Mapped[float] = mapped_column(Float)
    tp: Mapped[float] = mapped_column(Float)
    open_time: Mapped[datetime] = mapped_column(DateTime)
    close_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    strategy_name: Mapped[str] = mapped_column(String(50))
    ai_sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_sentiment_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class NewsSentiment(Base):
    __tablename__ = "news_sentiments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    headline: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sentiment_label: Mapped[str] = mapped_column(String(20))  # bullish/bearish/neutral
    sentiment_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class AIOptimizationLog(Base):
    __tablename__ = "ai_optimization_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    current_params: Mapped[str] = mapped_column(Text)  # JSON string
    suggested_params: Mapped[str] = mapped_column(Text)  # JSON string
    rationale: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    backtest_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON backtest comparison
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class MacroData(Base):
    __tablename__ = "macro_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    series_id: Mapped[str] = mapped_column(String(50), index=True)
    series_name: Mapped[str] = mapped_column(String(200))
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    value: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class MLModelLog(Base):
    __tablename__ = "ml_model_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100))
    timeframe: Mapped[str] = mapped_column(String(10))
    train_start: Mapped[datetime] = mapped_column(DateTime)
    train_end: Mapped[datetime] = mapped_column(DateTime)
    test_start: Mapped[datetime] = mapped_column(DateTime)
    test_end: Mapped[datetime] = mapped_column(DateTime)
    metrics: Mapped[str] = mapped_column(Text)  # JSON
    feature_importance: Mapped[str] = mapped_column(Text)  # JSON
    model_path: Mapped[str] = mapped_column(String(255))
    model_binary: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class BotEvent(Base):
    __tablename__ = "bot_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[BotEventType] = mapped_column(Enum(BotEventType))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class MLPredictionLog(Base):
    __tablename__ = "ml_prediction_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    model_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    symbol: Mapped[str] = mapped_column(String(20))
    predicted_signal: Mapped[int] = mapped_column(Integer)  # -1, 0, 1
    confidence: Mapped[float] = mapped_column(Float)
    actual_outcome: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # filled later
    was_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class OrderAudit(Base):
    __tablename__ = "order_audits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20))
    order_type: Mapped[str] = mapped_column(String(10))  # BUY / SELL
    requested_lot: Mapped[float] = mapped_column(Float)
    requested_sl: Mapped[float] = mapped_column(Float)
    requested_tp: Mapped[float] = mapped_column(Float)
    expected_price: Mapped[float] = mapped_column(Float)
    fill_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ticket: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # FILLED / REJECTED / TIMEOUT / ERROR
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signal_source: Mapped[str] = mapped_column(String(50))  # strategy name
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
