"""API router assembly."""

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.universe import router as universe_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(universe_router)
