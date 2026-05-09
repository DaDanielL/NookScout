"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI application without opening external connections."""
    resolved_settings = settings or get_settings()
    application = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
    )
    application.state.settings = resolved_settings
    application.include_router(api_router)
    return application


app = create_app()
