"""
OpenAI-compatible client — drop-in alternative to sdk_client.py.

Works with any OpenAI-format API: OpenAI, GLM (智谱), Ollama, LiteLLM, etc.
Two entry points matching sdk_client interface:
  - openai_complete(): simple prompt → text (sentiment, analysis)
  - openai_agent_loop(): multi-turn with MCP tool calling
"""

import json
import time
from typing import Any

from loguru import logger
from openai import AsyncOpenAI

from app.config import settings

# Lazy singleton — created on first use so settings are loaded
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        kwargs: dict[str, Any] = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        _client = AsyncOpenAI(**kwargs)
    return _client


def reset_client() -> None:
    """Reset the singleton (call after settings change)."""
    global _client
    _client = None


async def openai_complete(
    prompt: str,
    system_prompt: str,
    model: str | None = None,
    max_turns: int = 1,
    agent_id: str = "unknown",
) -> str | None:
    """Simple prompt → text response. No tools. For sentiment analysis."""
    from app.ai.usage_logger import log_ai_usage

    model = model or settings.openai_model
    start_time = time.time()
    usage: dict[str, Any] | None = None
    success = True

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        result = response.choices[0].message.content or ""
        usage = _extract_usage(response)

        if not result:
            success = False
            logger.warning(f"OpenAI complete: empty response for agent={agent_id}")

        await log_ai_usage(
            agent_id=agent_id,
            model=model,
            usage=usage,
            cost_usd_sdk=None,
            duration_ms=int((time.time() - start_time) * 1000),
            turns=1,
            tool_calls_count=0,
            success=success,
        )

        return result or None

    except Exception as e:
        logger.error(f"OpenAI complete error: {e}")
        await log_ai_usage(
            agent_id=agent_id,
            model=model,
            usage=usage,
            cost_usd_sdk=None,
            duration_ms=int((time.time() - start_time) * 1000),
            turns=0,
            tool_calls_count=0,
            success=False,
        )
        return None


async def openai_agent_loop(
    prompt: str,
    system_prompt: str,
    model: str | None = None,
    allowed_tools: list[str] | None = None,
    max_turns: int = 15,
    timeout: int = 120,
    agent_id: str = "unknown",
) -> dict[str, Any]:
    """Multi-turn agent loop with MCP tool calling via OpenAI function calling.

    Tools are loaded from the MCP server's tool registry and converted to
    OpenAI function-calling format. The agent iterates until it produces a
    final text response or hits max_turns/timeout.

    Returns dict matching sdk_agent_loop format:
        {response, tool_calls, turns, duration_s}
    """
    from app.ai.usage_logger import log_ai_usage

    model = model or settings.openai_model_orchestrator
    start_time = time.time()
    tool_calls_log: list[dict] = []
    turns = 0
    total_usage: dict[str, int] = {
        "input_tokens": 0,
        "output_tokens": 0,
    }
    success = True

    try:
        client = _get_client()
        tools_spec = _get_openai_tools(allowed_tools)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        for _ in range(max_turns):
            if time.time() - start_time > timeout:
                logger.warning(f"OpenAI agent timeout after {timeout}s")
                success = False
                break

            create_kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
            }
            if tools_spec:
                create_kwargs["tools"] = tools_spec

            response = await client.chat.completions.create(**create_kwargs)
            turns += 1

            # Accumulate usage
            if response.usage:
                total_usage["input_tokens"] += response.usage.prompt_tokens
                total_usage["output_tokens"] += response.usage.completion_tokens

            choice = response.choices[0]
            msg = choice.message

            # If no tool calls, we have the final response
            if not msg.tool_calls:
                text = msg.content or ""
                duration = round(time.time() - start_time, 1)

                await log_ai_usage(
                    agent_id=agent_id,
                    model=model,
                    usage=total_usage,
                    cost_usd_sdk=None,
                    duration_ms=int(duration * 1000),
                    turns=turns,
                    tool_calls_count=len(tool_calls_log),
                    success=success,
                )

                return {
                    "response": text or "No response",
                    "tool_calls": tool_calls_log,
                    "turns": turns,
                    "duration_s": duration,
                    "cost_usd": None,
                }

            # Process tool calls
            messages.append(msg.model_dump())

            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}

                logger.info(f"[Agent] Tool: {fn_name}")
                tool_calls_log.append({"tool": fn_name, "input": fn_args})

                # Execute the tool via MCP registry
                tool_result = await _execute_tool(fn_name, fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_result, default=str),
                })

        # Exhausted max_turns
        duration = round(time.time() - start_time, 1)
        # Try to get whatever text is in the last message
        last_text = ""
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "assistant" and m.get("content"):
                last_text = m["content"]
                break

        await log_ai_usage(
            agent_id=agent_id,
            model=model,
            usage=total_usage,
            cost_usd_sdk=None,
            duration_ms=int(duration * 1000),
            turns=turns,
            tool_calls_count=len(tool_calls_log),
            success=success,
        )

        return {
            "response": last_text or "Max turns reached",
            "tool_calls": tool_calls_log,
            "turns": turns,
            "duration_s": duration,
            "cost_usd": None,
        }

    except Exception as e:
        logger.error(f"OpenAI agent error: {e}")
        duration = round(time.time() - start_time, 1)
        await log_ai_usage(
            agent_id=agent_id,
            model=model,
            usage=total_usage if any(total_usage.values()) else None,
            cost_usd_sdk=None,
            duration_ms=int(duration * 1000),
            turns=turns,
            tool_calls_count=len(tool_calls_log),
            success=False,
        )
        return {
            "response": f"Agent error: {e}",
            "tool_calls": tool_calls_log,
            "turns": turns,
            "duration_s": duration,
            "error": str(e),
        }


# ─── Tool helpers ──────────────────────────────────────────────────────────────

_TOOL_REGISTRY: dict[str, Any] | None = None


def _get_tool_registry() -> dict[str, Any]:
    """Lazy-load tool functions from the MCP server module."""
    global _TOOL_REGISTRY
    if _TOOL_REGISTRY is not None:
        return _TOOL_REGISTRY

    from mcp_server.server import mcp
    _TOOL_REGISTRY = {}
    for tool in mcp._tool_manager._tools.values():
        _TOOL_REGISTRY[tool.name] = tool
    return _TOOL_REGISTRY


def _get_openai_tools(allowed_tools: list[str] | None) -> list[dict]:
    """Convert MCP tool definitions to OpenAI function-calling format."""
    registry = _get_tool_registry()
    tools = []

    for name, tool in registry.items():
        if allowed_tools and name not in allowed_tools:
            continue

        # Build JSON Schema for parameters from the tool's input schema
        params = {"type": "object", "properties": {}, "required": []}
        schema = getattr(tool, "parameters", None) or {}
        if isinstance(schema, dict):
            params = schema
        elif hasattr(tool, "fn"):
            # Fallback: inspect function signature
            import inspect
            sig = inspect.signature(tool.fn)
            props = {}
            req = []
            for pname, param in sig.parameters.items():
                if pname in ("ctx", "context"):
                    continue
                ptype = "string"
                annotation = param.annotation
                if annotation is not inspect.Parameter.empty:
                    if annotation in (int, float):
                        ptype = "number"
                    elif annotation is bool:
                        ptype = "boolean"
                props[pname] = {"type": ptype}
                if param.default is inspect.Parameter.empty:
                    req.append(pname)
            params = {"type": "object", "properties": props}
            if req:
                params["required"] = req

        fn_def: dict[str, Any] = {
            "name": name,
            "parameters": params,
        }
        desc = getattr(tool, "description", None)
        if desc:
            fn_def["description"] = desc[:1024]

        tools.append({"type": "function", "function": fn_def})

    return tools


async def _execute_tool(name: str, arguments: dict) -> Any:
    """Execute an MCP tool by name and return its result."""
    registry = _get_tool_registry()
    tool = registry.get(name)
    if not tool:
        return {"error": f"Unknown tool: {name}"}

    try:
        fn = tool.fn
        import asyncio
        if asyncio.iscoroutinefunction(fn):
            result = await fn(**arguments)
        else:
            result = fn(**arguments)
        return result
    except Exception as e:
        logger.error(f"Tool {name} error: {e}")
        return {"error": str(e)}


def _extract_usage(response: Any) -> dict[str, int] | None:
    """Extract token usage from OpenAI response."""
    if not response.usage:
        return None
    return {
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
    }
