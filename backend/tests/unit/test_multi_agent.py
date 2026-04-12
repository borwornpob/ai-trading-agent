"""
Unit tests for mcp_server/agents/ — multi-agent architecture.

Tests the orchestrator, specialist agents, and base agent loop.
Mocks the Claude Code SDK to avoid real API calls.
"""

import sys
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest

from mcp_server.agents.base import MODEL_ORCHESTRATOR, MODEL_SPECIALIST


# ─── Mock SDK types for testing ──────────────────────────────────────────────

@dataclass
class MockTextBlock:
    text: str
    type: str = "text"

@dataclass
class MockToolUseBlock:
    name: str
    input: dict
    id: str = "tool_1"
    type: str = "tool_use"

@dataclass
class MockAssistantMessage:
    content: list
    model: str = "test"
    type: str = "assistant"

@dataclass
class MockResultMessage:
    result: str
    num_turns: int
    duration_ms: int = 1000
    duration_api_ms: int = 500
    is_error: bool = False
    session_id: str = "test"
    total_cost_usd: float = 0.0
    usage: dict = None
    subtype: str = "result"
    type: str = "result"


async def _mock_query_simple(text: str):
    """Create a mock SDK query that returns a simple text response."""
    async def _gen(*args, **kwargs):
        yield MockAssistantMessage(content=[MockTextBlock(text=text)])
        yield MockResultMessage(result=text, num_turns=1)
    return _gen


class TestToolSubsets:
    """Verify each specialist gets the right tools and no execution tools."""

    def test_all_tools_defined_in_sdk(self):
        """Verify all tool names referenced by agents exist in SDK tools."""
        from mcp_server.sdk_tools import ALL_SDK_TOOLS
        all_names = {t.name for t in ALL_SDK_TOOLS}

        from mcp_server.agents.technical_analyst import TOOL_NAMES as tech_tools
        from mcp_server.agents.fundamental_analyst import TOOL_NAMES as fund_tools
        from mcp_server.agents.risk_analyst import TOOL_NAMES as risk_tools
        from mcp_server.agents.orchestrator import ORCHESTRATOR_TOOL_NAMES as orch_tools

        for name in tech_tools:
            assert name in all_names, f"Technical tool '{name}' not in SDK tools"
        for name in fund_tools:
            assert name in all_names, f"Fundamental tool '{name}' not in SDK tools"
        for name in risk_tools:
            assert name in all_names, f"Risk tool '{name}' not in SDK tools"
        for name in orch_tools:
            assert name in all_names, f"Orchestrator tool '{name}' not in SDK tools"

    def test_technical_has_no_execution_tools(self):
        from mcp_server.agents.technical_analyst import TOOL_NAMES
        execution_tools = {"place_order", "modify_position", "close_position"}
        assert not set(TOOL_NAMES) & execution_tools

    def test_fundamental_has_no_execution_tools(self):
        from mcp_server.agents.fundamental_analyst import TOOL_NAMES
        execution_tools = {"place_order", "modify_position", "close_position"}
        assert not set(TOOL_NAMES) & execution_tools

    def test_risk_has_no_execution_tools(self):
        from mcp_server.agents.risk_analyst import TOOL_NAMES
        execution_tools = {"place_order", "modify_position", "close_position"}
        assert not set(TOOL_NAMES) & execution_tools

    def test_orchestrator_has_execution_tools(self):
        from mcp_server.agents.orchestrator import ORCHESTRATOR_TOOL_NAMES
        assert "place_order" in ORCHESTRATOR_TOOL_NAMES
        assert "log_decision" in ORCHESTRATOR_TOOL_NAMES

    def test_technical_has_indicator_tools(self):
        from mcp_server.agents.technical_analyst import TOOL_NAMES
        assert "run_full_analysis" in TOOL_NAMES
        assert "get_tick" in TOOL_NAMES

    def test_fundamental_has_sentiment_tools(self):
        from mcp_server.agents.fundamental_analyst import TOOL_NAMES
        assert "get_sentiment" in TOOL_NAMES
        assert "get_performance" in TOOL_NAMES

    def test_risk_has_portfolio_tools(self):
        from mcp_server.agents.risk_analyst import TOOL_NAMES
        assert "get_account" in TOOL_NAMES
        assert "validate_trade" in TOOL_NAMES
        assert "check_correlation" in TOOL_NAMES


class TestModelSelection:
    def test_specialist_uses_haiku(self):
        assert "haiku" in MODEL_SPECIALIST.lower()

    def test_orchestrator_uses_sonnet(self):
        assert "sonnet" in MODEL_ORCHESTRATOR.lower()


class TestBaseAgentLoop:
    @pytest.mark.asyncio
    async def test_returns_error_without_sdk(self):
        from mcp_server.agents.base import run_agent_loop
        with patch("mcp_server.agents.base._SDK_AVAILABLE", False):
            result = await run_agent_loop(
                system_prompt="test",
                user_message="test",
            )
            assert "not available" in result["response"].lower()
            assert result["turns"] == 0

    @pytest.mark.asyncio
    async def test_handles_text_response(self):
        """When SDK returns a text response, extract it."""
        from mcp_server.agents.base import run_agent_loop

        async def mock_query(*args, **kwargs):
            yield MockAssistantMessage(content=[MockTextBlock("HOLD recommended")])
            yield MockResultMessage(result="HOLD recommended", num_turns=1)

        with (
            patch("mcp_server.agents.base._SDK_AVAILABLE", True),
            patch("mcp_server.agents.base.sdk_query", mock_query),
            patch("mcp_server.agents.base.create_trading_mcp_server", return_value=MagicMock()),
        ):
            result = await run_agent_loop(
                system_prompt="test",
                user_message="Analyze GOLD",
            )

        assert "HOLD recommended" in result["response"]
        assert result["turns"] == 1

    @pytest.mark.asyncio
    async def test_handles_tool_use(self):
        """SDK returns tool use blocks, verify they're tracked."""
        from mcp_server.agents.base import run_agent_loop

        async def mock_query(*args, **kwargs):
            yield MockAssistantMessage(content=[
                MockToolUseBlock(name="get_tick", input={"symbol": "GOLD"})
            ])
            yield MockAssistantMessage(content=[
                MockTextBlock("GOLD at 2450, BUY signal")
            ])
            yield MockResultMessage(result="BUY", num_turns=2)

        with (
            patch("mcp_server.agents.base._SDK_AVAILABLE", True),
            patch("mcp_server.agents.base.sdk_query", mock_query),
            patch("mcp_server.agents.base.create_trading_mcp_server", return_value=MagicMock()),
        ):
            result = await run_agent_loop(
                system_prompt="test",
                user_message="Analyze GOLD",
                tool_names=["get_tick"],
            )

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool"] == "get_tick"

    @pytest.mark.asyncio
    async def test_handles_sdk_error(self):
        """SDK errors should be caught gracefully."""
        from mcp_server.agents.base import run_agent_loop

        async def mock_query_error(*args, **kwargs):
            raise RuntimeError("CLI not found")
            yield  # make it a generator

        with (
            patch("mcp_server.agents.base._SDK_AVAILABLE", True),
            patch("mcp_server.agents.base.sdk_query", mock_query_error),
            patch("mcp_server.agents.base.create_trading_mcp_server", return_value=MagicMock()),
        ):
            result = await run_agent_loop(
                system_prompt="test",
                user_message="test",
            )

        assert "error" in result


class TestOrchestratorSynthesis:
    def test_build_synthesis_message(self):
        from mcp_server.agents.orchestrator import _build_synthesis_message

        msg = _build_synthesis_message(
            job_type="candle_analysis",
            job_input={"symbol": "GOLD", "timeframe": "M15"},
            symbol="GOLD",
            timeframe="M15",
            technical_report="RSI: 65, EMA bullish crossover",
            fundamental_report="Sentiment: bullish 0.72",
            risk_report="APPROVED, 0.05 lot recommended",
        )

        assert "Technical Analysis Report" in msg
        assert "RSI: 65" in msg
        assert "bullish 0.72" in msg
        assert "APPROVED" in msg

    def test_synthesis_with_reflection(self):
        from mcp_server.agents.orchestrator import _build_synthesis_message

        msg = _build_synthesis_message(
            job_type="candle_analysis",
            job_input={"symbol": "GOLD"},
            symbol="GOLD",
            timeframe="M15",
            technical_report="bullish",
            fundamental_report="neutral",
            risk_report="approved",
            reflection_report="Win rate 70% last 7 days",
        )
        assert "Reflection" in msg
        assert "Win rate 70%" in msg


class TestMultiAgentIntegration:
    @pytest.mark.asyncio
    async def test_orchestrator_runs_specialists_and_synthesizes(self):
        from mcp_server.agents.orchestrator import run_multi_agent

        mock_tech = AsyncMock(return_value={
            "response": "RSI 65, EMA bullish. Signal: BUY 0.7 confidence",
            "tool_calls": [{"tool": "run_full_analysis"}],
            "turns": 2,
        })
        mock_fund = AsyncMock(return_value={
            "response": "Sentiment bullish 0.72. Bias: BULLISH",
            "tool_calls": [{"tool": "get_sentiment"}],
            "turns": 2,
        })
        mock_risk = AsyncMock(return_value={
            "response": "Balance 10k. Verdict: APPROVED",
            "tool_calls": [{"tool": "get_account"}],
            "turns": 3,
        })

        mock_orch = {
            "response": "BUY 0.05 GOLD",
            "tool_calls": [],
            "turns": 3,
            "duration_s": 2.5,
        }

        with (
            patch("mcp_server.agents.orchestrator.reflector.reflect", AsyncMock(return_value={"response": "7d win rate 65%", "tool_calls": [], "turns": 2})),
            patch("mcp_server.agents.orchestrator.technical_analyst.analyze", mock_tech),
            patch("mcp_server.agents.orchestrator.fundamental_analyst.analyze", mock_fund),
            patch("mcp_server.agents.orchestrator.risk_analyst.analyze", mock_risk),
            patch("mcp_server.agents.orchestrator.run_agent_loop", AsyncMock(return_value=mock_orch)),
        ):
            result = await run_multi_agent(
                job_type="candle_analysis",
                job_input={"symbol": "GOLD", "timeframe": "M15"},
            )

        assert "decision" in result
        assert "specialists" in result
        assert "technical" in result["specialists"]
        assert "RSI 65" in result["specialists"]["technical"]["report"]

    @pytest.mark.asyncio
    async def test_specialist_error_handled_gracefully(self):
        from mcp_server.agents.orchestrator import run_multi_agent

        with (
            patch("mcp_server.agents.orchestrator.reflector.reflect", AsyncMock(return_value={"response": "", "tool_calls": [], "turns": 0})),
            patch("mcp_server.agents.orchestrator.technical_analyst.analyze", AsyncMock(side_effect=Exception("timeout"))),
            patch("mcp_server.agents.orchestrator.fundamental_analyst.analyze", AsyncMock(return_value={"response": "neutral", "tool_calls": [], "turns": 1})),
            patch("mcp_server.agents.orchestrator.risk_analyst.analyze", AsyncMock(return_value={"response": "caution", "tool_calls": [], "turns": 1})),
            patch("mcp_server.agents.orchestrator.run_agent_loop", AsyncMock(return_value={"response": "HOLD", "tool_calls": [], "turns": 1, "duration_s": 1.0})),
        ):
            result = await run_multi_agent(
                job_type="candle_analysis",
                job_input={"symbol": "GOLD"},
            )

        assert "decision" in result
        assert result.get("errors") is not None
        assert "technical" in result["errors"]


class TestAgentEntrypointModes:
    @pytest.mark.asyncio
    async def test_multi_mode(self):
        from app.runner.agent_entrypoint import execute_job

        mock_result = {"decision": "HOLD", "total_duration_s": 5.0, "orchestrator_turns": 3, "total_tool_calls": 8}

        with (
            patch.dict(os.environ, {"AGENT_MODE": "multi"}),
            patch("app.runner.agent_entrypoint._MULTI_AGENT_AVAILABLE", True),
            patch("app.runner.agent_entrypoint._AGENT_AVAILABLE", True),
            patch("app.runner.agent_entrypoint.run_multi_agent", create=True, new=AsyncMock(return_value=mock_result)),
            patch("app.runner.agent_entrypoint.init_broker", create=True),
        ):
            result = await execute_job(1, "candle_analysis", {"symbol": "GOLD"}, 1)
            assert result["decision"] == "HOLD"

    @pytest.mark.asyncio
    async def test_single_mode(self):
        from app.runner.agent_entrypoint import execute_job

        mock_result = {"decision": "BUY GOLD", "turns": 5, "duration_s": 3.0, "tool_calls": []}

        import app.runner.agent_entrypoint as ep
        original = getattr(ep, "run_agent", None)
        ep.run_agent = AsyncMock(return_value=mock_result)
        try:
            os.environ.pop("AGENT_MODE", None)
            with patch.object(ep, "_AGENT_AVAILABLE", True), patch.object(ep, "init_broker", lambda *a: None, create=True):
                result = await execute_job(1, "candle_analysis", {"symbol": "GOLD"}, 1)
            assert result["decision"] == "BUY GOLD"
        finally:
            if original:
                ep.run_agent = original

    @pytest.mark.asyncio
    async def test_stub_mode_no_sdk(self):
        from app.runner.agent_entrypoint import execute_job

        with patch("app.runner.agent_entrypoint._AGENT_AVAILABLE", False):
            result = await execute_job(1, "candle_analysis", {"symbol": "GOLD"}, 1)
            assert result["status"] == "stub"
