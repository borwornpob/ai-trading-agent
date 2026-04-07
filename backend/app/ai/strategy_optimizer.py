"""
Strategy Optimizer — weekly AI-powered parameter optimization.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import AIClient
from app.ai.prompts import OPTIMIZATION_SYSTEM_PROMPT
from app.db.models import AIOptimizationLog, Trade


@dataclass
class OptimizationResult:
    assessment: str
    current_params: dict
    suggested_params: dict
    confidence: float
    reasoning: str
    log_id: int | None = None

    def to_dict(self) -> dict:
        return {
            "assessment": self.assessment,
            "current_params": self.current_params,
            "suggested_params": self.suggested_params,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "log_id": self.log_id,
        }


# Valid parameter ranges for validation
PARAM_RANGES = {
    "fast_period": (5, 50),
    "slow_period": (20, 200),
    "rsi_period": (5, 30),
    "rsi_overbought": (60, 85),
    "rsi_oversold": (15, 40),
    "sl_multiplier": (0.5, 3.0),
    "tp_multiplier": (1.0, 5.0),
}


class StrategyOptimizer:
    def __init__(self, ai_client: AIClient, db_session: AsyncSession):
        self.ai = ai_client
        self.db = db_session

    async def build_performance_summary(self, days: int = 7) -> str:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(Trade).where(Trade.open_time >= cutoff).order_by(Trade.open_time)
        )
        trades = result.scalars().all()

        if not trades:
            return "No trades in the last {days} days."

        total = len(trades)
        closed = [t for t in trades if t.profit is not None]
        wins = [t for t in closed if t.profit > 0]
        losses = [t for t in closed if t.profit <= 0]

        avg_profit = sum(t.profit for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.profit for t in losses) / len(losses) if losses else 0
        total_profit = sum(t.profit for t in closed) if closed else 0
        win_rate = len(wins) / len(closed) * 100 if closed else 0

        # Profit factor
        gross_profit = sum(t.profit for t in wins) if wins else 0
        gross_loss = abs(sum(t.profit for t in losses)) if losses else 0
        pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        summary = f"""Period: last {days} days
Total trades: {total}
Closed trades: {len(closed)}
Win rate: {win_rate:.1f}%
Average profit: {avg_profit:.2f}
Average loss: {avg_loss:.2f}
Total profit: {total_profit:.2f}
Profit factor: {pf:.2f}"""
        return summary

    async def optimize(self, current_params: dict) -> OptimizationResult | None:
        summary = await self.build_performance_summary()
        user_prompt = f"Current performance:\n{summary}\n\nCurrent params: {json.dumps(current_params)}"

        result = self.ai.complete_json(OPTIMIZATION_SYSTEM_PROMPT, user_prompt, max_tokens=512)
        if result is None:
            logger.warning("AI optimization failed")
            return None

        # Validate suggested params
        suggested = result.get("suggested_params", {})
        for key, (low, high) in PARAM_RANGES.items():
            if key in suggested:
                val = suggested[key]
                if isinstance(val, (int, float)):
                    suggested[key] = max(low, min(high, val))

        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=7)

        # Save to DB
        try:
            log = AIOptimizationLog(
                period_start=period_start,
                period_end=now,
                current_params=json.dumps(current_params),
                suggested_params=json.dumps(suggested),
                rationale=result.get("reasoning", ""),
                confidence=float(result.get("confidence", 0.0)),
                applied=False,
            )
            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)
            log_id = log.id
        except Exception as e:
            logger.error(f"Failed to save optimization log: {e}")
            await self.db.rollback()
            log_id = None

        return OptimizationResult(
            assessment=result.get("assessment", ""),
            current_params=current_params,
            suggested_params=suggested,
            confidence=float(result.get("confidence", 0.0)),
            reasoning=result.get("reasoning", ""),
            log_id=log_id,
        )
