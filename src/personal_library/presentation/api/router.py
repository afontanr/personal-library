from fastapi import APIRouter

from personal_library.presentation.api.routes import books, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(books.router)
