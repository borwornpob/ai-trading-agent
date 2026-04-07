"""
Bot control API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/bot", tags=["bot"])

# Bot engine will be injected via app.state
_bot = None


def set_bot(bot):
    global _bot
    _bot = bot


def get_bot():
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    return _bot


class StrategyUpdate(BaseModel):
    name: str
    params: dict | None = None


class SettingsUpdate(BaseModel):
    use_ai_filter: bool | None = None
    ai_confidence_threshold: float | None = None


@router.post("/start")
async def start_bot():
    bot = get_bot()
    await bot.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_bot():
    bot = get_bot()
    await bot.stop()
    return {"status": "stopped"}


@router.post("/emergency-stop")
async def emergency_stop():
    bot = get_bot()
    result = await bot.emergency_stop()
    return {"status": "emergency_stopped", "result": result}


@router.get("/status")
async def get_status():
    bot = get_bot()
    status = bot.get_status()
    # Add sentiment if available
    if bot.sentiment_analyzer:
        sentiment = await bot.sentiment_analyzer.get_latest_sentiment()
        status["sentiment"] = sentiment.to_dict()
    return status


@router.put("/strategy")
async def update_strategy(data: StrategyUpdate):
    bot = get_bot()
    try:
        await bot.update_strategy(data.name, data.params)
        return {"status": "updated", "strategy": data.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/settings")
async def update_settings(data: SettingsUpdate):
    bot = get_bot()
    await bot.update_settings(
        use_ai_filter=data.use_ai_filter,
        ai_confidence_threshold=data.ai_confidence_threshold,
    )
    return {"status": "updated"}
