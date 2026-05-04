from functools import lru_cache

from fastapi import Depends, Request

from personal_library.application.use_cases.lookup_book import LookupBookByIsbn
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


def get_lookup_book_use_case(
    book_repository: BookRepository = Depends(get_book_repository),
) -> LookupBookByIsbn:
    return LookupBookByIsbn(book_repository=book_repository)
