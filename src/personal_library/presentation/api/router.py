from fastapi import APIRouter

from personal_library.presentation.api.routes import (
    books,
    collection,
    health,
    sagas,
    to_buy,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(books.router)
api_router.include_router(collection.router)
api_router.include_router(to_buy.router)
api_router.include_router(sagas.router)
