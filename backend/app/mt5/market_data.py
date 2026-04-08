"""
Market Data Service — fetches tick and OHLCV data via MT5 Bridge.
"""

import asyncio
from typing import Callable

import pandas as pd
from loguru import logger

from app.mt5.connector import MT5BridgeConnector


class MarketDataService:
    def __init__(self, connector: MT5BridgeConnector):
        self.connector = connector

    async def get_current_tick(self, symbol: str) -> dict | None:
        result = await self.connector.get_tick(symbol)
        if result.get("success"):
            return result["data"]
        logger.warning(f"Failed to get tick for {symbol}: {result.get('error')}")
        return None

    async def get_ohlcv(self, symbol: str, timeframe: str = "M15", count: int = 100) -> pd.DataFrame:
        result = await self.connector.get_ohlcv(symbol, timeframe, count)
        if not result.get("success") or not result.get("data"):
            logger.warning(f"Failed to get OHLCV for {symbol}: {result.get('error')}")
            return pd.DataFrame()

        df = pd.DataFrame(result["data"])
        df = df.assign(time=pd.to_datetime(df["time"])).set_index("time")
        return df

    async def stream_ticks(self, symbol: str, callback: Callable, interval: float = 1.0):
        while True:
            tick = await self.get_current_tick(symbol)
            if tick:
                await callback(tick)
            await asyncio.sleep(interval)
