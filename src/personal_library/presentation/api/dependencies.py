import httpx
from fastapi import Depends

from personal_library.domain.ports.book_repository import BookRepository
from personal_library.infrastructure.adapters.http.google_books_client import (
    GoogleBooksClient,
)
from personal_library.infrastructure.config.settings import Settings


def get_settings() -> Settings:
    return Settings()


def get_book_repository(
    settings: Settings = Depends(get_settings),
) -> BookRepository:
    http_client = httpx.AsyncClient()
    return GoogleBooksClient(http_client=http_client, settings=settings)
