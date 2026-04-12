"""
Base agent — shared agent loop used by all specialist agents and the orchestrator.

Uses Claude Code SDK (claude-code-sdk) which authenticates via Claude Max
subscription through the CLI. No API key needed.
"""

import json
import time
from typing import Any

from loguru import logger

from mcp_server.sdk_tools import create_trading_mcp_server, filter_sdk_tools

# Lazy import to handle missing SDK gracefully
_SDK_AVAILABLE = False
try:
    from claude_code_sdk import (
        query as sdk_query,
        ClaudeCodeOptions,
        AssistantMessage,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
    )
    from claude_code_sdk._errors import MessageParseError
    _SDK_AVAILABLE = True
except ImportError:
    pass


# ─── Model Constants ─────────────────────────────────────────────────────────

MODEL_ORCHESTRATOR = "claude-sonnet-4-20250514"
MODEL_SPECIALIST = "claude-haiku-4-5-20251001"


# ─── Shared Agent Loop ──────────────────────────────────────────────────────

async def run_agent_loop(
    system_prompt: str,
    user_message: str,
    tools: list | None = None,
    tool_names: list[str] | None = None,
    model: str = MODEL_SPECIALIST,
    max_turns: int = 15,
    timeout: int = 120,
    **kwargs,
) -> dict:
    """Run an agent loop using Claude Code SDK.

    Args:
        system_prompt: Agent's system prompt (role definition)
        user_message: The task/query for the agent
        tools: List of SDK tool objects (from sdk_tools.py)
        tool_names: Alternative: list of tool names to filter from ALL_SDK_TOOLS
        model: Claude model to use
        max_turns: Maximum conversation turns
        timeout: Timeout in seconds

    Returns:
        Dict with response text, tool calls made, and metadata.
    """
    if not _SDK_AVAILABLE:
        return {"response": "Claude Code SDK not available", "tool_calls": [], "turns": 0}

    # Build tools list
    if tools is None and tool_names is not None:
        tools = filter_sdk_tools(tool_names)

    # Build MCP server with selected tools
    mcp_server = create_trading_mcp_server(tools)

    # Build allowed tool names for SDK
    allowed = [t.name for t in (tools or [])]

    options = ClaudeCodeOptions(
        system_prompt=system_prompt,
        model=model,
        max_turns=max_turns,
        mcp_servers={"trading": mcp_server},
        allowed_tools=allowed if allowed else None,
        permission_mode="bypassPermissions",
    )

    tool_calls_made: list[dict] = []
    final_text = ""
    turns = 0
    start_time = time.time()
    max_retries = 3

    for attempt in range(max_retries):
        try:
            async for msg in sdk_query(prompt=user_message, options=options):
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    logger.warning(f"Agent timeout after {elapsed:.0f}s")
                    break

                msg_type = getattr(msg, "type", "")
                if msg_type == "assistant":
                    turns += 1
                    for block in getattr(msg, "content", []):
                        block_type = getattr(block, "type", "")
                        if block_type == "text" and hasattr(block, "text"):
                            final_text = block.text
                        elif block_type == "tool_use" and hasattr(block, "name"):
                            tool_calls_made.append({
                                "tool": block.name,
                                "input": getattr(block, "input", {}),
                            })
                            logger.info(f"[Agent] Tool: {block.name}")

                elif msg_type == "result":
                    if hasattr(msg, "result") and msg.result:
                        final_text = msg.result
                    turns = getattr(msg, "num_turns", turns)
                    break

            # If we got a response, don't retry
            if final_text:
                break

        except Exception as e:
            err_str = str(e)
            root_cause = e
            if hasattr(e, "exceptions"):
                root_cause = e.exceptions[0] if e.exceptions else e
                err_str = str(root_cause)

            is_transport = "ProcessTransport" in err_str or "not ready for writing" in err_str
            is_rate_limit = "rate_limit" in err_str.lower() or "MessageParseError" in type(root_cause).__name__

            if is_transport and attempt < max_retries - 1:
                wait_s = (attempt + 1) * 5
                logger.warning(f"SDK transport error (attempt {attempt + 1}/{max_retries}), retrying in {wait_s}s...")
                import asyncio as _aio
                await _aio.sleep(wait_s)
                continue
            elif is_rate_limit:
                logger.warning(f"Rate limited — response may be partial: {err_str[:100]}")
                break
            else:
                logger.error(f"Agent loop error: {err_str}")
                return {
                    "response": f"Agent error: {err_str}",
                    "tool_calls": tool_calls_made,
                    "turns": turns,
                    "error": err_str,
                }

    return {
        "response": final_text,
        "tool_calls": tool_calls_made,
        "turns": turns,
        "duration_s": round(time.time() - start_time, 1),
    }


def filter_tools(tool_names: list[str]) -> list:
    """Filter SDK tools by name (for backward compatibility)."""
    return filter_sdk_tools(tool_names)
