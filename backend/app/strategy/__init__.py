from pathlib import Path

from app.strategy.base import BaseStrategy
from app.strategy.breakout import BreakoutStrategy
from app.strategy.ema_crossover import EMACrossoverStrategy
from app.strategy.rsi_filter import RSIFilterStrategy

STRATEGIES: dict[str, type[BaseStrategy]] = {
    "ema_crossover": EMACrossoverStrategy,
    "rsi_filter": RSIFilterStrategy,
    "breakout": BreakoutStrategy,
}

# Conditionally register ML strategy if model exists
try:
    from app.strategy.ml_strategy import MLStrategy
    STRATEGIES["ml_signal"] = MLStrategy
except ImportError:
    pass  # lightgbm not installed


def get_strategy(name: str, params: dict | None = None) -> BaseStrategy:
    cls = STRATEGIES.get(name)
    if cls is None:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGIES.keys())}")
    return cls(**(params or {}))
