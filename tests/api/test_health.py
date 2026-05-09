"""Health endpoint tests."""

from datetime import datetime

from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


def test_health_endpoint_returns_non_secret_operational_payload(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app_name"] == "NookScout"
    assert payload["environment"] == "test"
    assert payload["market_data_provider"] == "massive"
    assert payload["timezone"] == "America/New_York"

    checked_at = datetime.fromisoformat(payload["checked_at"])
    assert checked_at.tzinfo is not None

    forbidden_fragments = ("key", "token", "secret", "password", "database_url")
    for field_name in payload:
        assert not any(fragment in field_name.lower() for fragment in forbidden_fragments)


def test_health_endpoint_uses_factory_injected_settings(test_settings: Settings) -> None:
    custom_settings = test_settings.model_copy(
        update={
            "app_name": "InjectedApp",
            "environment": "test",
            "timezone": "UTC",
            "market_data_provider": "test-provider",
        }
    )
    client = TestClient(create_app(custom_settings))

    payload = client.get("/health").json()

    assert payload["app_name"] == "InjectedApp"
    assert payload["environment"] == "test"
    assert payload["timezone"] == "UTC"
    assert payload["market_data_provider"] == "test-provider"
