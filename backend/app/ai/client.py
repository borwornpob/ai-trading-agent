"""
AI Client — unified wrapper for Claude Agent SDK and OpenAI-compatible APIs.
AI is an optional layer — all calls return None on failure.

Provider is controlled by settings.ai_provider:
  - "claude": Claude Agent SDK (Max subscription, no API key)
  - "openai": Any OpenAI-format API (OpenAI, GLM, Ollama, etc.)
"""

import json
import re

from loguru import logger

from app.config import settings

# Default models per provider
_CLAUDE_MODEL = "claude-haiku-4-5-20251001"


def _get_model() -> str:
    if settings.ai_provider == "openai":
        return settings.openai_model
    return _CLAUDE_MODEL


class AIClient:
    """AI client supporting Claude (Max subscription) and OpenAI-compatible APIs."""

    async def complete_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 256,
        agent_id: str = "sentiment",
    ) -> str | None:
        try:
            if settings.ai_provider == "openai":
                from mcp_server.openai_client import openai_complete
                return await openai_complete(
                    user_prompt, system_prompt, model=_get_model(), agent_id=agent_id,
                )
            else:
                from mcp_server.sdk_client import sdk_complete
                return await sdk_complete(
                    user_prompt, system_prompt, model=_CLAUDE_MODEL, agent_id=agent_id,
                )
        except Exception as e:
            logger.error(f"AI call failed (provider={settings.ai_provider}): {e}")
            return None

    async def complete_json_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 256,
        agent_id: str = "sentiment",
    ) -> dict | None:
        text = await self.complete_async(system_prompt, user_prompt, max_tokens, agent_id=agent_id)
        if text is None:
            return None
        try:
            cleaned = text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"AI JSON parse failed: {e}\nRaw: {text[:200]}")
            return None
