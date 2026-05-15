from functools import lru_cache

from fastapi import Depends, Request

from personal_library.application.use_cases.lookup_book import LookupBookByIsbn
from personal_library.application.use_cases.save_book import SaveBookToCollection
from personal_library.domain.ports.book_repository import BookRepository
from personal_library.domain.ports.collection_repository import CollectionRepository
from personal_library.infrastructure.adapters.http.google_books_client import (
    GoogleBooksClient,
)
from personal_library.infrastructure.adapters.db.sqlite_collection_repository import (
    SqliteCollectionRepository,
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


def get_collection_repository(
    request: Request,
) -> CollectionRepository:
    return request.app.state.collection_repository


def get_save_book_use_case(
    collection_repository: CollectionRepository = Depends(get_collection_repository),
) -> SaveBookToCollection:
    return SaveBookToCollection(collection_repository=collection_repository)
