import logging
from typing import Optional

_LOGGER_INITIALIZED = False


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure the application's root logger.

    This function is safe to call multiple times and will only configure
    logging once.
    """
    global _LOGGER_INITIALIZED

    if _LOGGER_INITIALIZED:
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _LOGGER_INITIALIZED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a configured logger instance.
    """
    return logging.getLogger(name)