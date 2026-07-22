"""Tests for application logging configuration."""

import logging

import pytest

from app.core.config import Settings
from app.core.logging import HANDLER_NAME, LOGGER_NAME, configure_logging


@pytest.fixture(autouse=True)
def clean_application_logger() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    original_handlers = logger.handlers[:]
    original_level = logger.level
    original_propagate = logger.propagate
    logger.handlers.clear()
    yield
    logger.handlers.clear()
    logger.handlers.extend(original_handlers)
    logger.setLevel(original_level)
    logger.propagate = original_propagate


def test_configure_logging_is_idempotent() -> None:
    settings = Settings(app_name="AOS API", environment="test", log_level="INFO")

    configure_logging(settings)
    configure_logging(settings)

    logger = logging.getLogger(LOGGER_NAME)
    handlers = [handler for handler in logger.handlers if handler.name == HANDLER_NAME]
    assert len(handlers) == 1


def test_configure_logging_sets_level_and_format() -> None:
    settings = Settings(app_name="AOS API", environment="test", log_level="DEBUG")

    configure_logging(settings)

    logger = logging.getLogger(LOGGER_NAME)
    handler = logger.handlers[0]
    assert logger.level == logging.DEBUG
    assert handler.level == logging.DEBUG
    assert handler.formatter is not None
    assert handler.formatter._fmt == "%(asctime)s %(levelname)s %(name)s %(message)s"
