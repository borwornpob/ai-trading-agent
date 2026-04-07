"""
Scheduler — APScheduler jobs for bot operations.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.bot.engine import BotEngine


class BotScheduler:
    def __init__(self, bot: BotEngine):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

    def start(self):
        # Update price cache every 1 second
        self.scheduler.add_job(
            self._tick_job,
            "interval",
            seconds=1,
            id="bot_tick",
            max_instances=1,
            coalesce=True,
        )

        # Run strategy every 15 minutes (candle close)
        self.scheduler.add_job(
            self._candle_job,
            "cron",
            minute="0,15,30,45",
            id="bot_candle",
            max_instances=1,
            coalesce=True,
        )

        # Fetch sentiment every 15 minutes (offset by 2 min)
        self.scheduler.add_job(
            self._sentiment_job,
            "cron",
            minute="2,17,32,47",
            id="fetch_sentiment",
            max_instances=1,
            coalesce=True,
        )

        # Sync positions every 30 seconds
        self.scheduler.add_job(
            self._sync_job,
            "interval",
            seconds=30,
            id="sync_positions",
            max_instances=1,
            coalesce=True,
        )

        # Weekly optimization: Monday 06:00 UTC
        self.scheduler.add_job(
            self._weekly_optimize_job,
            "cron",
            day_of_week="mon",
            hour=6,
            minute=0,
            id="weekly_optimize",
            max_instances=1,
        )

        # Daily reset: midnight UTC
        self.scheduler.add_job(
            self._daily_reset_job,
            "cron",
            hour=0,
            minute=0,
            id="daily_reset",
            max_instances=1,
        )

        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self):
        self.scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    async def _tick_job(self):
        if self.bot.state.value != "RUNNING":
            return
        try:
            tick = await self.bot.market_data.get_current_tick(self.bot.symbol)
            if tick:
                await self.bot._push_event("price_update", tick)
        except Exception as e:
            logger.error(f"Tick job error: {e}")

    async def _candle_job(self):
        logger.debug("Candle job triggered")
        await self.bot.process_candle()

    async def _sentiment_job(self):
        logger.debug("Sentiment job triggered")
        await self.bot.fetch_and_analyze_sentiment()

    async def _sync_job(self):
        await self.bot.sync_positions()

    async def _weekly_optimize_job(self):
        logger.info("Weekly optimization triggered")
        # Will be wired to strategy optimizer in main.py
        pass

    async def _daily_reset_job(self):
        logger.info("Daily reset triggered")
        await self.bot.circuit_breaker.reset()
