"""Structured logging service using Loguru"""

import sys
from pathlib import Path

from loguru import logger

from src.core.config import get_config
from src.core.constants import LOG_FORMAT


class LoggerService:
    """Centralized logging service"""

    _initialized = False

    @classmethod
    def init(cls) -> None:
        """Initialize logging service"""
        if cls._initialized:
            return

        config = get_config()

        logger.remove()

        log_level = config.get("logging.level", "INFO")
        log_file = config.get("logging.log_file", "./logs/app.log")
        log_format = config.get("logging.format", "json")
        max_size = config.get("logging.max_file_size_mb", 100) * 1024 * 1024
        backup_count = config.get("logging.backup_count", 5)

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            sys.stderr,
            level=log_level,
            format=LOG_FORMAT,
            colorize=True,
        )

        logger.add(
            str(log_path),
            level=log_level,
            format=LOG_FORMAT if log_format == "text" else "<level>{message}</level>",
            rotation="10 MB",
            retention=backup_count,
            encoding="utf-8",
        )

        cls._initialized = True


def get_logger(name: str):
    """Get logger instance"""
    LoggerService.init()
    return logger.bind(name=name)
