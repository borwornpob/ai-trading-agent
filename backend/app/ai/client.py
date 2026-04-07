"""
AI Client — wrapper for Anthropic SDK (Claude Haiku).
AI is an optional layer — all calls return None on failure.
"""

import json
import re

import anthropic
from loguru import logger

from app.config import settings

MODEL = "claude-haiku-4-5-20251001"


class AIClient:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 256) -> str | None:
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
        text = self.complete(system_prompt, user_prompt, max_tokens)
        if text is None:
            return None
        try:
            # Strip markdown code fences if present
            cleaned = text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"AI JSON parse failed: {e}\nRaw: {text[:200]}")
            return None
