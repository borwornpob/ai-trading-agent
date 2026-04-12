"""
Agent configuration — sets up the Claude agent with trading tools.

Uses Claude Code SDK (claude-code-sdk) which authenticates via Claude Max
subscription through the CLI. No API key needed.
"""

import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from mcp_server.agents.base import run_agent_loop, MODEL_ORCHESTRATOR
from mcp_server.guardrails import AGENT_TIMEOUT, MAX_AGENT_TURNS


# ─── System Prompt ───────────────────────────────────────────────────────────

_SYSTEM_PROMPT: str | None = None


def _load_system_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        prompt_path = Path(__file__).parent / "system_prompt.md"
        _SYSTEM_PROMPT = prompt_path.read_text(encoding="utf-8")
    return _SYSTEM_PROMPT


# ─── Agent Entry Points ─────────────────────────────────────────────────────

async def run_agent(
    job_type: str,
    job_input: dict | None,
    oauth_token: str | None = None,
    model: str = MODEL_ORCHESTRATOR,
) -> dict:
    """Run the single-agent loop for a job using Claude Code SDK.

    Args:
        job_type: Type of job (e.g., "candle_analysis", "manual_analysis")
        job_input: Job parameters (e.g., {"symbol": "GOLD", "timeframe": "M15"})
        oauth_token: Unused (SDK uses CLI auth). Kept for backward compat.
        model: Claude model to use

    Returns:
        Dict with agent output (reasoning, decision, tool calls made).
    """
    system_prompt = _load_system_prompt()
    user_message = _build_user_message(job_type, job_input)

    result = await run_agent_loop(
        system_prompt=system_prompt,
        user_message=user_message,
        model=model,
        max_turns=MAX_AGENT_TURNS,
        timeout=AGENT_TIMEOUT,
    )

    return {
        "decision": result.get("response", "No decision"),
        "turns": result.get("turns", 0),
        "tool_calls": result.get("tool_calls", []),
        "duration_s": result.get("duration_s", 0),
    }


async def run_multi_agent(
    job_type: str,
    job_input: dict | None,
    oauth_token: str | None = None,
) -> dict:
    """Run the multi-agent pipeline (orchestrator + specialists).

    Delegates to the orchestrator which coordinates specialist agents.
    """
    from mcp_server.agents.orchestrator import run_multi_agent as _run
    return await _run(job_type, job_input, oauth_token)


# ─── Message Builder ────────────────────────────────────────────────────────

def _build_user_message(job_type: str, job_input: dict | None) -> str:
    """Build the initial user message for the agent based on job type."""
    input_str = json.dumps(job_input, default=str) if job_input else "{}"

    if job_type == "candle_analysis":
        symbol = (job_input or {}).get("symbol", "GOLD")
        timeframe = (job_input or {}).get("timeframe", "M15")
        return (
            f"A new {timeframe} candle has closed for {symbol}. "
            f"Analyze the current market conditions and decide whether to trade.\n\n"
            f"Job input: {input_str}"
        )
    elif job_type == "manual_analysis":
        symbol = (job_input or {}).get("symbol", "GOLD")
        return (
            f"The owner has requested a manual analysis of {symbol}. "
            f"Provide a thorough market analysis with your trading recommendation.\n\n"
            f"Job input: {input_str}"
        )
    elif job_type == "weekly_review":
        return (
            "Perform a weekly trading review. Analyze the past week's performance, "
            "identify patterns, and suggest adjustments to the trading approach.\n\n"
            f"Job input: {input_str}"
        )
    else:
        return f"Job type: {job_type}\nInput: {input_str}"
