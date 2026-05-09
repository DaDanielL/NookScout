"""Settings tests."""

from typing import Any, cast

import pytest
from pydantic import ValidationError

from app.core.settings import Settings

ENV_NAMES = (
    "NOOKSCOUT_APP_NAME",
    "NOOKSCOUT_ENVIRONMENT",
    "NOOKSCOUT_LOG_LEVEL",
    "NOOKSCOUT_TIMEZONE",
    "NOOKSCOUT_DATABASE_URL",
    "NOOKSCOUT_MARKET_DATA_PROVIDER",
    "MASSIVE_API_KEY",
    "MASSIVE_API_BASE_URL",
    "MASSIVE_STOCKS_PLAN",
    "MASSIVE_DATA_RECENCY",
    "MASSIVE_REQUEST_TIMEOUT_SECONDS",
    "MASSIVE_MAX_RETRIES",
)


def build_settings(**values: object) -> Settings:
    """Construct settings while bypassing local `.env` during tests."""
    settings_type = cast(Any, Settings)
    return settings_type(_env_file=None, **values)


def test_settings_use_safe_defaults_without_env_file(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)

    settings = build_settings()

    assert settings.app_name == "NookScout"
    assert settings.environment == "local"
    assert settings.timezone == "America/New_York"
    assert settings.market_data_provider == "massive"
    assert settings.massive_api_key is None


def test_settings_parse_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOOKSCOUT_ENVIRONMENT", "test")
    monkeypatch.setenv("NOOKSCOUT_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("NOOKSCOUT_TIMEZONE", "UTC")
    monkeypatch.setenv("NOOKSCOUT_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("MASSIVE_REQUEST_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("MASSIVE_MAX_RETRIES", "1")

    settings = build_settings()

    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"
    assert settings.timezone == "UTC"
    assert str(settings.timezone_info) == "UTC"
    assert settings.database_url == "sqlite+pysqlite:///:memory:"
    assert settings.massive_request_timeout_seconds == 12
    assert settings.massive_max_retries == 1


def test_settings_mask_secret_values() -> None:
    settings = build_settings(massive_api_key="super-secret-value")

    assert "super-secret-value" not in repr(settings)
    assert settings.massive_api_key is not None
    assert str(settings.massive_api_key) == "**********"


def test_settings_reject_unknown_timezone() -> None:
    with pytest.raises(ValidationError):
        build_settings(timezone="Mars/Base")
