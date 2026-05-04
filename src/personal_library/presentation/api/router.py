from fastapi import APIRouter

from personal_library.presentation.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
