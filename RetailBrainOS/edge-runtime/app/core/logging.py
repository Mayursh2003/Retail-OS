import logging
import sys

_LOGGING_CONFIGURED = False


def configure_logging() -> None:
    """
    Configure centralized logging for the Edge Runtime.
    """

    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    _LOGGING_CONFIGURED = True