"""
SDK tool definitions — wraps existing MCP tool handlers as Claude Code SDK tools.

Uses @tool decorator from claude-code-sdk to register tools that the agent
can call via the in-process MCP server. Each tool delegates to the existing
handler functions in mcp_server/tools/*.
"""

import asyncio
import json
from typing import Any

from claude_code_sdk import create_sdk_mcp_server, tool

from mcp_server.tools import market_data, indicators, risk, broker, portfolio
from mcp_server.tools import sentiment, history, journal, learning, session, strategy_gen


# ─── Helper ──────────────────────────────────────────────────────────────────

def _result(data: Any) -> dict:
    """Format tool result for SDK MCP server."""
    if isinstance(data, str):
        text = data
    else:
        text = json.dumps(data, default=str)
    return {"content": [{"type": "text", "text": text}]}


async def _call(handler, **kwargs) -> dict:
    """Call a handler (sync or async) and return formatted result."""
    try:
        result = handler(**kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return _result(result)
    except Exception as e:
        return {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}], "is_error": True}


# ─── Market Data Tools ───────────────────────────────────────────────────────

@tool("get_tick", "Get current bid/ask tick for a trading symbol", {"symbol": str})
async def sdk_get_tick(args):
    return await _call(market_data.get_tick, symbol=args["symbol"])


@tool("get_ohlcv", "Get OHLCV candlestick data", {"symbol": str, "timeframe": str, "count": int})
async def sdk_get_ohlcv(args):
    return await _call(market_data.get_ohlcv,
                       symbol=args["symbol"],
                       timeframe=args.get("timeframe", "M15"),
                       count=args.get("count", 100))


@tool("get_spread", "Get current spread for a symbol", {"symbol": str})
async def sdk_get_spread(args):
    return await _call(market_data.get_spread, symbol=args["symbol"])


# ─── Indicator Tools ─────────────────────────────────────────────────────────

@tool("run_full_analysis",
      "Run comprehensive technical analysis: EMA, RSI, ATR, ADX, Bollinger, Stochastic. Primary tool for market analysis.",
      {"symbol": str, "timeframe": str})
async def sdk_full_analysis(args):
    return await _call(indicators.full_analysis,
                       symbol=args["symbol"],
                       timeframe=args.get("timeframe", "M15"))


@tool("calculate_ema", "Calculate Exponential Moving Average", {"symbol": str, "period": int, "timeframe": str})
async def sdk_calculate_ema(args):
    return await _call(indicators.calculate_ema,
                       symbol=args["symbol"],
                       period=args.get("period", 20),
                       timeframe=args.get("timeframe", "M15"))


@tool("calculate_rsi", "Calculate Relative Strength Index (0-100)", {"symbol": str, "period": int, "timeframe": str})
async def sdk_calculate_rsi(args):
    return await _call(indicators.calculate_rsi,
                       symbol=args["symbol"],
                       period=args.get("period", 14),
                       timeframe=args.get("timeframe", "M15"))


@tool("calculate_atr", "Calculate Average True Range (volatility)", {"symbol": str, "period": int, "timeframe": str})
async def sdk_calculate_atr(args):
    return await _call(indicators.calculate_atr,
                       symbol=args["symbol"],
                       period=args.get("period", 14),
                       timeframe=args.get("timeframe", "M15"))


# ─── Risk Tools ──────────────────────────────────────────────────────────────

@tool("validate_trade", "Check if a trade is allowed under risk rules",
      {"symbol": str, "signal": int, "current_positions": int, "daily_pnl": float, "balance": float})
async def sdk_validate_trade(args):
    return _result(risk.validate_trade(**args))


@tool("calculate_lot_size", "Calculate optimal position size based on risk",
      {"symbol": str, "balance": float, "sl_pips": float})
async def sdk_calculate_lot_size(args):
    return _result(risk.calculate_lot(**args))


@tool("calculate_sl_tp", "Calculate stop-loss and take-profit levels",
      {"symbol": str, "entry_price": float, "signal": int, "atr": float})
async def sdk_calculate_sl_tp(args):
    return _result(risk.calculate_sl_tp(**args))


# ─── Broker Tools (GUARDRAIL-GATED) ─────────────────────────────────────────

@tool("place_order", "Place a trade order. GUARDRAIL-GATED: validated before execution.",
      {"symbol": str, "order_type": str, "lot": float, "sl": float, "tp": float, "comment": str})
async def sdk_place_order(args):
    return await _call(broker.place_order,
                       symbol=args["symbol"],
                       order_type=args["order_type"],
                       lot=args["lot"],
                       sl=args["sl"],
                       tp=args["tp"],
                       comment=args.get("comment", ""))


@tool("modify_position", "Modify SL/TP of an existing position", {"ticket": int, "sl": float, "tp": float})
async def sdk_modify_position(args):
    return await _call(broker.modify_position,
                       ticket=args["ticket"],
                       sl=args.get("sl"),
                       tp=args.get("tp"))


@tool("close_position", "Close a position by ticket number", {"ticket": int})
async def sdk_close_position(args):
    return await _call(broker.close_position, ticket=args["ticket"])


@tool("get_positions", "Get open positions, optionally filtered by symbol", {"symbol": str})
async def sdk_get_positions(args):
    return await _call(broker.get_positions, symbol=args.get("symbol"))


# ─── Portfolio Tools ─────────────────────────────────────────────────────────

@tool("get_account", "Get account summary: balance, equity, margin, profit", {})
async def sdk_get_account(args):
    return await _call(portfolio.get_account)


@tool("get_exposure", "Get portfolio exposure breakdown by symbol", {})
async def sdk_get_exposure(args):
    return await _call(portfolio.get_exposure)


@tool("check_correlation", "Check for correlation conflicts before trading",
      {"symbol": str, "signal": int, "active_positions": dict})
async def sdk_check_correlation(args):
    return _result(portfolio.check_correlation(**args))


# ─── Sentiment Tools ─────────────────────────────────────────────────────────

@tool("get_sentiment", "Get latest AI sentiment analysis (bullish/bearish/neutral)", {})
async def sdk_get_sentiment(args):
    return await _call(sentiment.get_latest_sentiment)


@tool("get_sentiment_history", "Get sentiment history for the past N days", {"days": int})
async def sdk_get_sentiment_history(args):
    return await _call(sentiment.get_sentiment_history, days=args.get("days", 7))


# ─── History Tools ───────────────────────────────────────────────────────────

@tool("get_trade_history", "Get recent trade history", {"days": int, "symbol": str})
async def sdk_get_trade_history(args):
    return await _call(history.get_trade_history,
                       days=args.get("days", 7),
                       symbol=args.get("symbol"))


@tool("get_daily_pnl", "Get daily P&L summary", {"symbol": str})
async def sdk_get_daily_pnl(args):
    return await _call(history.get_daily_pnl, symbol=args.get("symbol"))


@tool("get_performance", "Get performance statistics (win rate, Sharpe, drawdown)", {"days": int, "symbol": str})
async def sdk_get_performance(args):
    return await _call(history.get_performance,
                       days=args.get("days", 30),
                       symbol=args.get("symbol"))


# ─── Journal Tools ───────────────────────────────────────────────────────────

@tool("log_decision", "Log a trading decision with reasoning. MUST be called for every decision.",
      {"symbol": str, "decision": str, "reasoning": str, "confidence": float})
async def sdk_log_decision(args):
    return await _call(journal.log_decision,
                       symbol=args["symbol"],
                       decision=args["decision"],
                       reasoning=args["reasoning"],
                       confidence=args.get("confidence"))


@tool("log_reasoning", "Log the agent's internal reasoning/thought process", {"thought_process": str})
async def sdk_log_reasoning(args):
    return await _call(journal.log_reasoning, thought_process=args["thought_process"])


# ─── Learning Tools (Phase E) ───────────────────────────────────────────────

@tool("analyze_recent_trades", "Analyze recent trade outcomes to identify patterns and strategy performance",
      {"days": int, "symbol": str})
async def sdk_analyze_recent_trades(args):
    return await _call(learning.analyze_recent_trades,
                       days=args.get("days", 7),
                       symbol=args.get("symbol"))


@tool("detect_regime", "Detect current market regime (trending/ranging/volatile/transitional)",
      {"symbol": str, "timeframe": str})
async def sdk_detect_regime(args):
    return await _call(learning.detect_regime,
                       symbol=args.get("symbol", "GOLD"),
                       timeframe=args.get("timeframe", "M15"))


# ─── Session Memory Tools (Phase E) ─────────────────────────────────────────

@tool("save_context", "Save session context for today's trading session", {"symbol": str, "context": dict})
async def sdk_save_context(args):
    return await _call(session.save_context, symbol=args["symbol"], context=args["context"])


@tool("get_context", "Retrieve today's session context for a symbol", {"symbol": str})
async def sdk_get_context(args):
    return await _call(session.get_context, symbol=args["symbol"])


@tool("save_learning", "Save a cross-session learning that persists for 7 days",
      {"learning_text": str, "category": str})
async def sdk_save_learning(args):
    return await _call(session.save_learning,
                       learning=args["learning_text"],
                       category=args.get("category", "general"))


@tool("get_learnings", "Retrieve cross-session learnings, optionally by category", {"category": str})
async def sdk_get_learnings(args):
    return await _call(session.get_learnings, category=args.get("category"))


# ─── Strategy Tools (Phase E) ───────────────────────────────────────────────

@tool("get_strategy_profiles", "Get all strategy profiles with regime suitability", {})
async def sdk_get_strategy_profiles(args):
    return _result(strategy_gen.get_strategy_profiles())


@tool("recommend_strategy", "Recommend the best strategy for the current market regime",
      {"regime": str, "symbol": str})
async def sdk_recommend_strategy(args):
    return _result(strategy_gen.recommend_strategy(
        regime=args["regime"], symbol=args.get("symbol", "GOLD")))


@tool("generate_strategy_config", "Generate a custom strategy config from a template with validated parameters",
      {"base_strategy": str, "param_overrides": dict, "name": str})
async def sdk_generate_strategy_config(args):
    return _result(strategy_gen.generate_strategy_config(
        base_strategy=args["base_strategy"],
        param_overrides=args.get("param_overrides"),
        name=args.get("name")))


@tool("generate_ensemble_config", "Generate a custom ensemble with specified strategy weights",
      {"weights": dict, "name": str})
async def sdk_generate_ensemble_config(args):
    return _result(strategy_gen.generate_ensemble_config(
        weights=args["weights"], name=args.get("name", "custom_ensemble")))


# ─── MCP Server Factory ─────────────────────────────────────────────────────

ALL_SDK_TOOLS = [
    # Market Data
    sdk_get_tick, sdk_get_ohlcv, sdk_get_spread,
    # Indicators
    sdk_full_analysis, sdk_calculate_ema, sdk_calculate_rsi, sdk_calculate_atr,
    # Risk
    sdk_validate_trade, sdk_calculate_lot_size, sdk_calculate_sl_tp,
    # Broker
    sdk_place_order, sdk_modify_position, sdk_close_position, sdk_get_positions,
    # Portfolio
    sdk_get_account, sdk_get_exposure, sdk_check_correlation,
    # Sentiment
    sdk_get_sentiment, sdk_get_sentiment_history,
    # History
    sdk_get_trade_history, sdk_get_daily_pnl, sdk_get_performance,
    # Journal
    sdk_log_decision, sdk_log_reasoning,
    # Learning
    sdk_analyze_recent_trades, sdk_detect_regime,
    # Session
    sdk_save_context, sdk_get_context, sdk_save_learning, sdk_get_learnings,
    # Strategy
    sdk_get_strategy_profiles, sdk_recommend_strategy,
    sdk_generate_strategy_config, sdk_generate_ensemble_config,
]


def create_trading_mcp_server(tools: list | None = None):
    """Create an in-process SDK MCP server with trading tools.

    Args:
        tools: Optional list of specific tools. Defaults to ALL_SDK_TOOLS.

    Returns:
        McpSdkServerConfig for use in ClaudeCodeOptions.mcp_servers
    """
    return create_sdk_mcp_server(
        name="trading-tools",
        tools=tools or ALL_SDK_TOOLS,
    )


def filter_sdk_tools(tool_names: list[str]) -> list:
    """Filter ALL_SDK_TOOLS by name."""
    name_set = set(tool_names)
    return [t for t in ALL_SDK_TOOLS if t.name in name_set]
