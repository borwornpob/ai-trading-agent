"""
AI usage logger — writes AIUsageLog rows after each SDK call.
Failures are swallowed: logging must never break the agent call.
"""

from typing import Any

from loguru import logger

from app.ai.pricing import calculate_cost
from app.db.models import AIUsageLog
from app.db.session import async_session


def _extract_tokens(usage: dict[str, Any] | None) -> tuple[int, int, int, int]:
    if not usage:
        return 0, 0, 0, 0
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
    cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)
    return input_tokens, output_tokens, cache_read, cache_write


async def log_ai_usage(
    *,
    agent_id: str,
    model: str,
    usage: dict[str, Any] | None,
    cost_usd_sdk: float | None = None,
    duration_ms: int = 0,
    turns: int = 0,
    tool_calls_count: int = 0,
    success: bool = True,
) -> None:
    try:
        input_t, output_t, cache_r, cache_w = _extract_tokens(usage)
        cost_calc = calculate_cost(model, input_t, output_t, cache_r, cache_w)

        row = AIUsageLog(
            agent_id=agent_id,
            model=model,
            input_tokens=input_t,
            output_tokens=output_t,
            cache_read_tokens=cache_r,
            cache_write_tokens=cache_w,
            cost_usd_sdk=cost_usd_sdk,
            cost_usd_calc=cost_calc,
            duration_ms=duration_ms,
            turns=turns,
            tool_calls_count=tool_calls_count,
            success=success,
            raw_usage=usage,
        )
        async with async_session() as session:
            session.add(row)
            await session.commit()
    except Exception as e:
        logger.warning(f"log_ai_usage failed: {e}")
