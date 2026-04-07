"""
Risk Manager — lot sizing, SL/TP calculation, trade permission checks.
"""

from dataclasses import dataclass
from loguru import logger


@dataclass
class SLTPResult:
    sl: float
    tp: float


class RiskManager:
    def __init__(
        self,
        max_risk_per_trade: float = 0.01,
        max_daily_loss: float = 0.03,
        max_concurrent_trades: int = 3,
        max_lot: float = 1.0,
        use_ai_filter: bool = True,
        ai_confidence_threshold: float = 0.7,
    ):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_concurrent_trades = max_concurrent_trades
        self.max_lot = max_lot
        self.use_ai_filter = use_ai_filter
        self.ai_confidence_threshold = ai_confidence_threshold

    def calculate_lot_size(self, balance: float, sl_pips: float, pip_value: float = 1.0) -> float:
        if sl_pips <= 0:
            return 0.01
        lot = (balance * self.max_risk_per_trade) / (sl_pips * pip_value * 100)
        lot = round(min(lot, self.max_lot), 2)
        return max(lot, 0.01)

    def calculate_sl_tp(
        self, entry_price: float, signal: int, atr: float, sl_mult: float = 1.5, tp_mult: float = 2.0
    ) -> SLTPResult:
        if signal == 1:  # BUY
            sl = entry_price - (atr * sl_mult)
            tp = entry_price + (atr * tp_mult)
        else:  # SELL
            sl = entry_price + (atr * sl_mult)
            tp = entry_price - (atr * tp_mult)
        return SLTPResult(sl=round(sl, 2), tp=round(tp, 2))

    def can_open_trade(
        self,
        current_positions: int,
        daily_pnl: float,
        balance: float,
        signal: int = 0,
        ai_sentiment: dict | None = None,
    ) -> tuple[bool, str]:
        # Check max concurrent trades
        if current_positions >= self.max_concurrent_trades:
            return False, f"Max concurrent trades reached ({self.max_concurrent_trades})"

        # Check daily loss limit
        max_loss = balance * self.max_daily_loss
        if daily_pnl <= -max_loss:
            return False, f"Daily loss limit reached ({daily_pnl:.2f} <= -{max_loss:.2f})"

        # AI sentiment filter (optional)
        if self.use_ai_filter and ai_sentiment and signal != 0:
            confidence = ai_sentiment.get("confidence", 0)
            label = ai_sentiment.get("label", "neutral")

            if confidence >= self.ai_confidence_threshold:
                if signal == 1 and label == "bearish":
                    return False, f"AI sentiment bearish (confidence: {confidence:.0%}) — BUY signal filtered"
                if signal == -1 and label == "bullish":
                    return False, f"AI sentiment bullish (confidence: {confidence:.0%}) — SELL signal filtered"

        return True, "OK"
