"""Integration Status API — test connectivity to all external services."""

import time

import httpx
from fastapi import APIRouter, Request
from loguru import logger

from app.config import settings

router = APIRouter(prefix="/api/integration", tags=["integration"])


async def _test_anthropic() -> dict:
    """Test Anthropic API connectivity."""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": settings.anthropic_api_key, "anthropic-version": "2023-06-01"},
            )
        latency = int((time.time() - start) * 1000)
        if resp.status_code == 200:
            return {"name": "Anthropic API", "status": "connected", "latency_ms": latency, "detail": "Claude AI ready"}
        return {"name": "Anthropic API", "status": "error", "latency_ms": latency, "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"name": "Anthropic API", "status": "error", "latency_ms": 0, "detail": str(e)}


async def _test_mt5() -> dict:
    """Test MT5 Bridge connectivity."""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{settings.mt5_bridge_url}/health",
                headers={"X-Bridge-Key": settings.mt5_bridge_api_key},
            )
        latency = int((time.time() - start) * 1000)
        if resp.status_code == 200:
            return {"name": "MT5 Bridge", "status": "connected", "latency_ms": latency, "detail": f"VPS: {settings.mt5_bridge_url}"}
        return {"name": "MT5 Bridge", "status": "error", "latency_ms": latency, "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"name": "MT5 Bridge", "status": "error", "latency_ms": 0, "detail": str(e)}


async def _test_redis(request: Request) -> dict:
    """Test Redis connectivity."""
    start = time.time()
    try:
        import redis.asyncio as redis_lib
        client = redis_lib.from_url(settings.redis_url)
        await client.ping()
        latency = int((time.time() - start) * 1000)
        await client.aclose()
        return {"name": "Redis", "status": "connected", "latency_ms": latency, "detail": "Cache + queue ready"}
    except Exception as e:
        return {"name": "Redis", "status": "error", "latency_ms": 0, "detail": str(e)}


async def _test_db() -> dict:
    """Test PostgreSQL connectivity."""
    start = time.time()
    try:
        from sqlalchemy import text
        from app.db.session import async_session
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        latency = int((time.time() - start) * 1000)
        return {"name": "PostgreSQL", "status": "connected", "latency_ms": latency, "detail": "Database ready"}
    except Exception as e:
        return {"name": "PostgreSQL", "status": "error", "latency_ms": 0, "detail": str(e)}


async def _test_binance() -> dict:
    """Test Binance API connectivity."""
    start = time.time()
    try:
        base_url = settings.binance_base_url if hasattr(settings, "binance_base_url") else ""
        if not base_url:
            return {"name": "Binance", "status": "disabled", "latency_ms": 0, "detail": "Not configured"}
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{base_url}/api/v3/ping")
        latency = int((time.time() - start) * 1000)
        if resp.status_code == 200:
            label = "Testnet" if "testnet" in base_url else "Production"
            return {"name": "Binance", "status": "connected", "latency_ms": latency, "detail": f"{label}: {base_url}"}
        return {"name": "Binance", "status": "error", "latency_ms": latency, "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"name": "Binance", "status": "error", "latency_ms": 0, "detail": str(e)}


@router.get("/status")
async def get_integration_status(request: Request):
    """Test all integrations and return status."""
    import asyncio
    results = await asyncio.gather(
        _test_anthropic(),
        _test_mt5(),
        _test_redis(request),
        _test_db(),
        _test_binance(),
    )
    return {"services": list(results)}


@router.get("/test/{service}")
async def test_service(service: str, request: Request):
    """Test a single service."""
    testers = {
        "anthropic": _test_anthropic,
        "mt5": _test_mt5,
        "redis": lambda: _test_redis(request),
        "db": _test_db,
        "binance": _test_binance,
    }
    tester = testers.get(service)
    if not tester:
        return {"name": service, "status": "error", "detail": f"Unknown service: {service}"}
    return await tester()
