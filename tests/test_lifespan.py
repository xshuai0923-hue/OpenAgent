"""Tests for application lifespan management."""

import logging

import pytest

from app.core.config import Settings
from app.core.logging import LOGGER_NAME
from app.main import app


@pytest.mark.anyio
async def test_lifespan_sets_settings_and_logs_startup_and_shutdown(
    capsys: pytest.CaptureFixture[str],
) -> None:
    async with app.router.lifespan_context(app):
        assert isinstance(app.state.settings, Settings)

    captured = capsys.readouterr()
    assert "Application started" in captured.err
    assert "Application stopped" in captured.err

    logging.getLogger(LOGGER_NAME).handlers.clear()
