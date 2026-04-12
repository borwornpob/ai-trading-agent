"""Shared utilities for MCP tools."""

import os
import sys

# Add backend to path once (instead of in every tool module)
_backend_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)


def backend_url() -> str:
    """Get the backend API URL from env or default."""
    return os.environ.get("BACKEND_URL", "http://localhost:8000")


def init_mcp_tools(redis_client) -> None:
    """Initialize all MCP tools that require Redis. Idempotent — safe to call once at startup."""
    from mcp_server.tools.broker import init_broker
    from mcp_server.tools.session import init_session
    init_broker(redis_client)
    init_session(redis_client)
