"""
Model pricing (USD per 1M tokens) — used to compute equivalent API cost.

Covers Claude (Max subscription) and OpenAI-compatible models.
For custom/self-hosted models where pricing is unknown, returns None.
"""

PRICING: dict[str, dict[str, float]] = {
    # Claude
    "claude-sonnet-4-20250514": {
        "input": 3.0,
        "output": 15.0,
        "cache_read": 0.3,
        "cache_write": 3.75,
    },
    "claude-haiku-4-5-20251001": {
        "input": 1.0,
        "output": 5.0,
        "cache_read": 0.1,
        "cache_write": 1.25,
    },
    # OpenAI
    "gpt-4o": {
        "input": 2.5,
        "output": 10.0,
        "cache_read": 1.25,
        "cache_write": 0.0,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "cache_read": 0.075,
        "cache_write": 0.0,
    },
    "gpt-4.1": {
        "input": 2.0,
        "output": 8.0,
        "cache_read": 0.5,
        "cache_write": 0.0,
    },
    "gpt-4.1-mini": {
        "input": 0.4,
        "output": 1.6,
        "cache_read": 0.1,
        "cache_write": 0.0,
    },
    "gpt-4.1-nano": {
        "input": 0.1,
        "output": 0.4,
        "cache_read": 0.025,
        "cache_write": 0.0,
    },
    # GLM (智谱)
    "glm-4-plus": {
        "input": 0.7,
        "output": 0.7,
        "cache_read": 0.0,
        "cache_write": 0.0,
    },
    "glm-4-flash": {
        "input": 0.0,
        "output": 0.0,
        "cache_read": 0.0,
        "cache_write": 0.0,
    },
}


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read: int = 0,
    cache_write: int = 0,
) -> float | None:
    p = PRICING.get(model)
    if not p:
        return None
    return (
        input_tokens * p["input"]
        + output_tokens * p["output"]
        + cache_read * p.get("cache_read", 0)
        + cache_write * p.get("cache_write", 0)
    ) / 1_000_000
