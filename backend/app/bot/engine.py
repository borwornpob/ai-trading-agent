"""
Bot Engine — main trading loop integrating strategy, risk, AI sentiment, and orders.
"""

import enum
import json
from datetime import datetime, timezone

import redis.asyncio as redis
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.news_sentiment import NewsSentimentAnalyzer
from app.config import settings
from app.db.models import BotEvent, BotEventType, Trade
from app.mt5.connector import MT5BridgeConnector
from app.mt5.market_data import MarketDataService
from app.mt5.order_executor import OrderExecutor
from app.news.fetcher import NewsFetcher
from app.risk.circuit_breaker import CircuitBreaker
from app.risk.manager import RiskManager
from app.strategy import get_strategy
from app.strategy.base import BaseStrategy


class BotState(str, enum.Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


class BotEngine:
    def __init__(
        self,
        connector: MT5BridgeConnector,
        db_session: AsyncSession,
        redis_client: redis.Redis,
    ):
        self.connector = connector
        self.market_data = MarketDataService(connector)
        self.executor = OrderExecutor(connector)
        self.db = db_session
        self.redis = redis_client
        self.circuit_breaker = CircuitBreaker(redis_client)

        # Initialize with defaults — can be updated via API
        self.strategy: BaseStrategy = get_strategy("ema_crossover")
        self.risk_manager = RiskManager(
            max_risk_per_trade=settings.max_risk_per_trade,
            max_daily_loss=settings.max_daily_loss,
            max_concurrent_trades=settings.max_concurrent_trades,
            max_lot=settings.max_lot,
            use_ai_filter=settings.use_ai_filter,
            ai_confidence_threshold=settings.ai_confidence_threshold,
        )
        self.sentiment_analyzer: NewsSentimentAnalyzer | None = None
        self.news_fetcher = NewsFetcher()

        self.state = BotState.STOPPED
        self.started_at: datetime | None = None
        self.last_signal_time: datetime | None = None
        self.symbol = settings.symbol
        self.timeframe = settings.timeframe

    def set_sentiment_analyzer(self, analyzer: NewsSentimentAnalyzer):
        self.sentiment_analyzer = analyzer

    async def start(self):
        if self.state == BotState.RUNNING:
            return
        self.state = BotState.RUNNING
        self.started_at = datetime.now(timezone.utc)
        await self._log_event(BotEventType.STARTED, "Bot started")
        logger.info(f"Bot started: strategy={self.strategy.name}, symbol={self.symbol}")

    async def stop(self):
        self.state = BotState.STOPPED
        await self._log_event(BotEventType.STOPPED, "Bot stopped")
        logger.info("Bot stopped")

    async def emergency_stop(self):
        self.state = BotState.STOPPED
        result = await self.executor.close_all_positions(self.symbol)
        await self._log_event(BotEventType.STOPPED, f"Emergency stop: {result}")
        logger.warning(f"EMERGENCY STOP executed: {result}")
        return result

    def get_status(self) -> dict:
        return {
            "state": self.state.value,
            "strategy": self.strategy.name,
            "strategy_params": self.strategy.get_params(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "use_ai_filter": self.risk_manager.use_ai_filter,
        }

    async def process_candle(self):
        """Main trading logic — called every candle close."""
        if self.state != BotState.RUNNING:
            return

        try:
            # 1. Check circuit breaker
            account = await self.connector.get_account()
            if not account.get("success"):
                logger.error("Cannot get account info")
                return

            balance = account["data"]["balance"]
            if await self.circuit_breaker.is_triggered(balance):
                self.state = BotState.PAUSED
                await self._log_event(BotEventType.CIRCUIT_BREAKER, "Circuit breaker triggered")
                return

            # 2. Fetch OHLCV and calculate signal
            df = await self.market_data.get_ohlcv(self.symbol, self.timeframe, 200)
            if df.empty:
                return

            df = self.strategy.calculate(df)
            if len(df) < 2:
                return

            signal = int(df.iloc[-2]["signal"])  # Previous bar's signal (confirmed candle)
            if signal == 0:
                return

            self.last_signal_time = datetime.now(timezone.utc)
            logger.info(f"Signal detected: {'BUY' if signal == 1 else 'SELL'}")

            # 3. Get AI sentiment (optional)
            ai_sentiment = None
            if self.sentiment_analyzer and self.risk_manager.use_ai_filter:
                sentiment = await self.sentiment_analyzer.get_latest_sentiment()
                if sentiment.confidence > 0:
                    ai_sentiment = {"label": sentiment.label, "confidence": sentiment.confidence}

            # 4. Check risk
            positions = await self.executor.get_open_positions(self.symbol)
            daily_pnl = await self.circuit_breaker.get_daily_pnl()

            can_trade, reason = self.risk_manager.can_open_trade(
                current_positions=len(positions),
                daily_pnl=daily_pnl,
                balance=balance,
                signal=signal,
                ai_sentiment=ai_sentiment,
            )
            if not can_trade:
                logger.info(f"Trade blocked: {reason}")
                return

            # 5. Calculate lot size and SL/TP
            atr = df.iloc[-2].get("atr", 10.0)
            tick = await self.market_data.get_current_tick(self.symbol)
            if not tick:
                return

            entry_price = tick["ask"] if signal == 1 else tick["bid"]
            sl_tp = self.risk_manager.calculate_sl_tp(entry_price, signal, atr)
            sl_pips = abs(entry_price - sl_tp.sl)
            lot = self.risk_manager.calculate_lot_size(balance, sl_pips)

            # 6. Place order
            order_type = "BUY" if signal == 1 else "SELL"
            comment = f"{self.strategy.name}"
            result = await self.executor.place_order(
                self.symbol, order_type, lot, sl_tp.sl, sl_tp.tp, comment
            )

            if result.get("success"):
                # 7. Save trade to DB
                sentiment_data = ai_sentiment or {}
                trade = Trade(
                    ticket=result["data"]["ticket"],
                    symbol=self.symbol,
                    type=order_type,
                    lot=lot,
                    open_price=entry_price,
                    sl=sl_tp.sl,
                    tp=sl_tp.tp,
                    open_time=datetime.now(timezone.utc),
                    strategy_name=self.strategy.name,
                    ai_sentiment_score=sentiment_data.get("confidence"),
                    ai_sentiment_label=sentiment_data.get("label"),
                )
                self.db.add(trade)
                await self.db.commit()

                await self._log_event(
                    BotEventType.TRADE_OPENED,
                    f"{order_type} {lot} {self.symbol} @ {entry_price} SL={sl_tp.sl} TP={sl_tp.tp}",
                )

                # Push event via Redis
                await self._push_event("bot_event", {
                    "type": "trade_opened",
                    "data": result["data"],
                    "sentiment": sentiment_data,
                })

        except Exception as e:
            logger.error(f"Bot engine error: {e}")
            self.state = BotState.ERROR
            await self._log_event(BotEventType.ERROR, str(e))

    async def fetch_and_analyze_sentiment(self):
        """Fetch news and run sentiment analysis."""
        if not self.sentiment_analyzer:
            return
        try:
            news = await self.news_fetcher.fetch_all_sources()
            if news:
                result = await self.sentiment_analyzer.analyze(news)
                logger.info(f"Sentiment: {result.label} (score={result.score}, confidence={result.confidence})")
                await self._push_event("sentiment_update", result.to_dict())
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")

    async def sync_positions(self):
        """Sync open positions and update closed trades."""
        if self.state != BotState.RUNNING:
            return
        try:
            positions = await self.executor.get_open_positions(self.symbol)
            await self._push_event("position_update", {"positions": positions})
        except Exception as e:
            logger.error(f"Position sync error: {e}")

    async def update_strategy(self, name: str, params: dict | None = None):
        self.strategy = get_strategy(name, params)
        logger.info(f"Strategy updated: {name} params={params}")

    async def update_settings(self, use_ai_filter: bool | None = None, ai_confidence_threshold: float | None = None):
        if use_ai_filter is not None:
            self.risk_manager.use_ai_filter = use_ai_filter
        if ai_confidence_threshold is not None:
            self.risk_manager.ai_confidence_threshold = ai_confidence_threshold

    async def _log_event(self, event_type: BotEventType, message: str):
        try:
            event = BotEvent(event_type=event_type, message=message)
            self.db.add(event)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    async def _push_event(self, channel: str, data: dict):
        try:
            await self.redis.publish(channel, json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to push event: {e}")
