"""
Logging configuration — structured JSON logging with loguru.
Call configure_logging() once at startup; applies globally to all logger imports.
"""

import sys
from pathlib import Path

from loguru import logger

from app.config import settings


def configure_logging():
    """Configure loguru sinks based on LOG_FORMAT setting."""
    # Remove default stderr sink
    logger.remove()

    log_format = settings.log_format.lower()
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Always add stderr sink (human-readable for dev, JSON for prod)
    if log_format == "json":
        logger.add(
            sys.stderr,
            serialize=True,
            level="INFO",
        )
    else:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG",
            colorize=True,
        )

    # Always add JSON file sink (for production log shipping)
    logger.add(
        str(log_dir / "bot.log"),
        serialize=True,
        rotation="50 MB",
        retention="7 days",
        compression="gz",
        level="INFO",
        enqueue=True,  # thread-safe async writing
    )

    # Separate error log for quick triage
    logger.add(
        str(log_dir / "errors.log"),
        serialize=True,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        level="ERROR",
        enqueue=True,
    )

    logger.info("Logging configured", format=log_format, log_dir=str(log_dir))
