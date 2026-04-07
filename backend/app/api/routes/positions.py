"""
Positions API routes.
"""

from fastapi import APIRouter

from app.api.routes.bot import get_bot

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("")
async def get_positions():
    bot = get_bot()
    positions = await bot.executor.get_open_positions(bot.symbol)
    return {"positions": positions}


@router.delete("/{ticket}")
async def close_position(ticket: int):
    bot = get_bot()
    result = await bot.executor.close_position(ticket)
    return result
