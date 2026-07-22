"""Tests for application configuration."""

import pytest

from app.core.config import APP_NAME, ENVIRONMENT, LOG_LEVEL, Settings, load_settings
from app.core.exceptions import ConfigurationError


def test_load_settings_uses_defaults() -> None:
    assert load_settings({}) == Settings(
        app_name=APP_NAME,
        environment=ENVIRONMENT,
        log_level=LOG_LEVEL,
    )


def test_load_settings_reads_environment() -> None:
    settings = load_settings({"AOS_ENVIRONMENT": "test", "AOS_LOG_LEVEL": "debug"})

    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"


def test_load_settings_rejects_invalid_log_level() -> None:
    with pytest.raises(ConfigurationError, match="Invalid LOG_LEVEL"):
        load_settings({"AOS_LOG_LEVEL": "verbose"})
