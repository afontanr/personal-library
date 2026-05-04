from functools import lru_cache

from fastapi import Depends, Request

from personal_library.domain.ports.book_repository import BookRepository
from personal_library.infrastructure.adapters.http.google_books_client import (
    GoogleBooksClient,
)
from personal_library.infrastructure.config.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_book_repository(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> BookRepository:
    http_client = request.app.state.http_client
    return GoogleBooksClient(http_client=http_client, settings=settings)
