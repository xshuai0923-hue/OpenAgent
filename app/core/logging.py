"""Application logging configuration."""

import logging
import logging.config

from app.core.config import Settings

LOGGER_NAME = "aos"
HANDLER_NAME = "aos_console"


def configure_logging(settings: Settings) -> None:
    """Configure the application console logger without duplicate handlers."""
    logger = logging.getLogger(LOGGER_NAME)
    existing_handler = next(
        (handler for handler in logger.handlers if handler.name == HANDLER_NAME),
        None,
    )
    if existing_handler is not None:
        existing_handler.setLevel(settings.log_level)
        logger.setLevel(settings.log_level)
        return

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                }
            },
            "handlers": {
                HANDLER_NAME: {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": settings.log_level,
                    "stream": "ext://sys.stderr",
                }
            },
            "loggers": {
                LOGGER_NAME: {
                    "handlers": [HANDLER_NAME],
                    "level": settings.log_level,
                    "propagate": False,
                }
            },
        }
    )
