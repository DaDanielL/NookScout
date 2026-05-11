"""Shared pytest fixtures."""

from collections.abc import Generator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


def build_test_settings(**values: object) -> Settings:
    """Construct settings while bypassing local `.env` during tests."""
    settings_type = cast(Any, Settings)
    return settings_type(_env_file=None, **values)


@pytest.fixture
def test_settings() -> Settings:
    """Return deterministic settings that do not depend on local secrets."""
    return build_test_settings(
        app_name="NookScout",
        environment="test",
        log_level="INFO",
        timezone="America/New_York",
        database_url="sqlite+pysqlite:///:memory:",
        market_data_provider="massive",
        massive_api_key=None,
        massive_api_base_url="https://api.polygon.io",
        massive_stocks_plan="starter",
        massive_data_recency="delayed",
        massive_request_timeout_seconds=30,
        massive_max_retries=3,
        predefined_universe_symbols=(),
        liquidity_min_price="5",
        liquidity_min_average_daily_volume=1_000_000,
        liquidity_min_dollar_volume="20000000",
        liquidity_min_market_cap="1000000000",
        liquidity_allowed_exchanges=("XNAS", "XNYS", "NASDAQ", "NYSE"),
        liquidity_average_volume_lookback_days=90,
    )


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """Return a TestClient wired to deterministic test settings."""
    application = create_app(test_settings)

    with TestClient(application) as test_client:
        yield test_client

    application.dependency_overrides.clear()
