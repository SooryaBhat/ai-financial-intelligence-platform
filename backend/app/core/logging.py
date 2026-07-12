"""
Structured logging configuration using Loguru.
Provides a pre-configured logger instance used throughout the application.
"""
import sys

from loguru import logger

from app.core.config import settings


def configure_logging() -> None:
    """
    Set up Loguru with structured JSON output for production
    and human-readable output for development.
    Called once at application startup in main.py.
    """
    logger.remove()  # Remove default handler

    log_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    # Always log to stdout
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=log_format,
        colorize=settings.is_development,
        serialize=settings.is_production,  # JSON in production
        enqueue=True,  # Thread-safe
        backtrace=settings.debug,
        diagnose=settings.debug,
    )

    # Optionally log to file
    if settings.log_file:
        logger.add(
            settings.log_file,
            level=settings.log_level,
            format=log_format,
            rotation="50 MB",
            retention="30 days",
            compression="gz",
            enqueue=True,
            serialize=True,  # Always JSON in file
        )

    logger.info(
        "Logging configured | env={} level={}",
        settings.app_env,
        settings.log_level,
    )


# Re-export the configured logger so the rest of the app can do:
#   from app.core.logging import logger
__all__ = ["logger", "configure_logging"]
