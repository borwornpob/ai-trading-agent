"""
Base agent — shared agent loop supporting Claude SDK and OpenAI-compatible APIs.

All specialist agents and the orchestrator use run_agent_loop().
Provider is controlled by settings.ai_provider.
"""

from typing import Any

from loguru import logger

from app.config import settings


# ─── Model Constants ─────────────────────────────────────────────────────────

# Claude models (used when ai_provider="claude")
_CLAUDE_ORCHESTRATOR = "claude-sonnet-4-20250514"
_CLAUDE_SPECIALIST = "claude-haiku-4-5-20251001"


def get_model_orchestrator() -> str:
    if settings.ai_provider == "openai":
        return settings.openai_model_orchestrator
    return _CLAUDE_ORCHESTRATOR


def get_model_specialist() -> str:
    if settings.ai_provider == "openai":
        return settings.openai_model
    return _CLAUDE_SPECIALIST


# Backward-compatible constants — read dynamically
# These are properties that re-evaluate on each access so existing imports
# like `from mcp_server.agents.base import MODEL_ORCHESTRATOR` keep working.
MODEL_ORCHESTRATOR = _CLAUDE_ORCHESTRATOR
MODEL_SPECIALIST = _CLAUDE_SPECIALIST


# ─── Shared Agent Loop ──────────────────────────────────────────────────────

async def run_agent_loop(
    system_prompt: str,
    user_message: str,
    tools: list[dict[str, Any]] | None = None,
    tool_names: list[str] | None = None,
    model: str | None = None,
    max_turns: int = 15,
    timeout: int = 120,
    agent_id: str = "unknown",
    **kwargs,
) -> dict:
    """Run an agent loop using the configured AI provider."""
    if settings.ai_provider == "openai":
        from mcp_server.openai_client import openai_agent_loop
        return await openai_agent_loop(
            prompt=user_message,
            system_prompt=system_prompt,
            model=model,
            allowed_tools=tool_names,
            max_turns=max_turns,
            timeout=timeout,
            agent_id=agent_id,
        )
    else:
        from mcp_server.sdk_client import sdk_agent_loop
        return await sdk_agent_loop(
            prompt=user_message,
            system_prompt=system_prompt,
            model=model or _CLAUDE_ORCHESTRATOR,
            allowed_tools=tool_names,
            max_turns=max_turns,
            timeout=timeout,
            agent_id=agent_id,
        )
