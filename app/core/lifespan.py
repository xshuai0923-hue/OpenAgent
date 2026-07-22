"""FastAPI application lifespan management."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import load_settings
from app.core.logging import LOGGER_NAME, configure_logging

logger = logging.getLogger(LOGGER_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and stop application foundation components."""
    settings = load_settings()
    configure_logging(settings)
    app.state.settings = settings
    logger.info("Application started")
    try:
        yield
    finally:
        logger.info("Application stopped")
