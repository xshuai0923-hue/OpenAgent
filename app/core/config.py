"""Application configuration loaded from environment variables."""

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass

from app.core.exceptions import ConfigurationError

APP_NAME = "AOS API"
ENVIRONMENT = "development"
LOG_LEVEL = "INFO"


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    app_name: str
    environment: str
    log_level: str


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Load and validate application settings."""
    source = os.environ if environ is None else environ
    environment = source.get("AOS_ENVIRONMENT", ENVIRONMENT).strip()
    log_level = source.get("AOS_LOG_LEVEL", LOG_LEVEL).strip().upper()

    if log_level not in logging.getLevelNamesMapping():
        raise ConfigurationError(f"Invalid LOG_LEVEL: {log_level!r}")

    return Settings(
        app_name=APP_NAME,
        environment=environment,
        log_level=log_level,
    )
