"""Tests for application exceptions."""

from app.core.exceptions import ApplicationError, ConfigurationError


def test_configuration_error_is_an_application_error() -> None:
    assert issubclass(ConfigurationError, ApplicationError)
