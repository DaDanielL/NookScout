"""Shared FastAPI dependencies."""

from typing import cast

from fastapi import Request

from app.core.settings import Settings, get_settings


def get_app_settings(request: Request) -> Settings:
    """Return application-scoped settings for request handlers."""
    if hasattr(request.app.state, "settings"):
        return cast(Settings, request.app.state.settings)
    return get_settings()
