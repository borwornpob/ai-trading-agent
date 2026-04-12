"""
AI Client — wrapper for Claude AI via Claude Code SDK or Anthropic API.

Supports two modes:
1. Claude Code SDK (Max subscription) — uses `claude` CLI, no API key needed
2. Anthropic API (fallback) — uses API key from config

AI is an optional layer — all calls return None on failure.
"""

import asyncio
import json
import re

from loguru import logger

from app.config import settings

MODEL = "claude-haiku-4-5-20251001"

# Check if Claude Code SDK is available
_SDK_AVAILABLE = False
try:
    from claude_code_sdk import query as sdk_query, ClaudeCodeOptions, AssistantMessage, TextBlock
    _SDK_AVAILABLE = True
except ImportError:
    pass

# Check if Anthropic API is available (fallback)
_API_AVAILABLE = False
try:
    import anthropic
    _API_AVAILABLE = True
except ImportError:
    pass


class AIClient:
    def __init__(self):
        self.client = None
        if _API_AVAILABLE and settings.anthropic_api_key:
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    @property
    def available(self) -> bool:
        return _SDK_AVAILABLE or self.client is not None

    async def complete_async(self, system_prompt: str, user_prompt: str, max_tokens: int = 256) -> str | None:
        """Async completion — tries SDK first, falls back to API."""
        # Try Claude Code SDK (Max subscription)
        if _SDK_AVAILABLE:
            try:
                text = ""
                async for msg in sdk_query(
                    prompt=user_prompt,
                    options=ClaudeCodeOptions(
                        system_prompt=system_prompt,
                        model=MODEL,
                        max_turns=1,
                    ),
                ):
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                text = block.text
                if text:
                    logger.info(f"AI call via SDK: {len(text)} chars")
                    return text
            except Exception as e:
                if "rate_limit" not in str(e).lower():
                    logger.warning(f"SDK AI call failed: {e}")

        # Fallback: Anthropic API
        if self.client:
            return self.complete(system_prompt, user_prompt, max_tokens)

        logger.warning("AI not available (no SDK or API key)")
        return None

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 256) -> str | None:
        """Sync completion via Anthropic API (legacy)."""
        if not self.client:
            logger.warning("AI client not configured (no API key)")
            return None
        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            logger.info(f"AI call: {input_tokens} in / {output_tokens} out tokens")
            return text
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return None

    def complete_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 256) -> dict | None:
        """Sync JSON completion (legacy)."""
        text = self.complete(system_prompt, user_prompt, max_tokens)
        if text is None:
            return None
        return self._parse_json(text)

    async def complete_json_async(self, system_prompt: str, user_prompt: str, max_tokens: int = 256) -> dict | None:
        """Async JSON completion."""
        text = await self.complete_async(system_prompt, user_prompt, max_tokens)
        if text is None:
            return None
        return self._parse_json(text)

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        try:
            cleaned = text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"AI JSON parse failed: {e}\nRaw: {text[:200]}")
            return None
