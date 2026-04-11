"""
Volatility Regime Detection — detects market regime and suggests parameter adjustments.
Uses ATR percentile + ADX to classify: trending_high_vol, trending_low_vol, ranging, normal.
"""

from app.constants import ADX_RANGING_THRESHOLD, HIGH_VOL_THRESHOLD, LOW_VOL_THRESHOLD


def detect_regime(atr_pct: float, adx_value: float) -> str:
    """
    Detect current market regime.

    Args:
        atr_pct: ATR as percentage of price (e.g., 0.5 = 0.5%)
        adx_value: ADX(14) value (0-100)

    Returns:
        One of: "trending_high_vol", "trending_low_vol", "ranging", "normal"
    """
    is_trending = adx_value >= ADX_RANGING_THRESHOLD
    is_high_vol = atr_pct > HIGH_VOL_THRESHOLD
    is_low_vol = atr_pct < LOW_VOL_THRESHOLD

    if is_trending and is_high_vol:
        return "trending_high_vol"
    elif is_trending and is_low_vol:
        return "trending_low_vol"
    elif not is_trending:
        return "ranging"
    else:
        return "normal"


# Strategy parameter adjustments per regime
REGIME_ADJUSTMENTS = {
    "trending_high_vol": {
        # Wider SL, wider trail, breakout-friendly
        "sl_atr_mult_factor": 1.3,
        "tp_atr_mult_factor": 1.5,
        "description": "Strong trend + high volatility — wider stops, let profits run",
    },
    "trending_low_vol": {
        # Tighter entries, normal SL
        "sl_atr_mult_factor": 1.0,
        "tp_atr_mult_factor": 1.2,
        "description": "Trend + low volatility — standard stops, slightly wider TP",
    },
    "ranging": {
        # Mean-reversion friendly, tighter SL/TP
        "sl_atr_mult_factor": 0.8,
        "tp_atr_mult_factor": 0.8,
        "description": "Ranging market — tighter stops and targets",
    },
    "normal": {
        # No adjustment
        "sl_atr_mult_factor": 1.0,
        "tp_atr_mult_factor": 1.0,
        "description": "Normal conditions — use base parameters",
    },
}


def get_regime_adjustments(regime: str) -> dict:
    """Get SL/TP adjustment factors for the given regime."""
    return REGIME_ADJUSTMENTS.get(regime, REGIME_ADJUSTMENTS["normal"])
