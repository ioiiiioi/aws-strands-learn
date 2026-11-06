"""Setup loguru: satu tempat, dipanggil sekali saat aplikasi mulai."""

import sys

from loguru import logger

from app.core.config import settings

FORMAT = (
    "<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | "
    "<cyan>{name}</cyan> - {message}"
)


def setup_logging() -> None:
    """Pasang sink stderr; level mengikuti APP_ENV. Aman dipanggil berulang."""
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG" if settings.APP_ENV == "development" else "INFO",
        format=FORMAT,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )
