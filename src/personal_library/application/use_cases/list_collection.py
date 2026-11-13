from dataclasses import dataclass
from enum import StrEnum

from personal_library.domain.model.collection_book import CollectionBook
from personal_library.domain.model.text import normalize_text
from personal_library.domain.ports.collection_repository import CollectionRepository


class CollectionOrder(StrEnum):
    DEFAULT = "defecto"
    AUTHOR = "autor"
    SAGA = "saga"

    @classmethod
    def from_param(cls, value: str | None) -> "CollectionOrder":
        try:
            return cls(value)
        except ValueError:
            return cls.DEFAULT


@dataclass(frozen=True)
class SagaGroup:
    """Books of one saga in Orden por saga; ``name`` is None for books without saga."""

    name: str | None
    books: list[CollectionBook]


def _author_sort_key(book: CollectionBook) -> tuple:
    author = normalize_text(book.authors[0]) if book.authors else ""
    title = normalize_text(book.title)
    if not author:
        return (1, "", 0, "", title)
    date = book.published_date or ""
    return (0, author, 0 if date else 1, date, title)


def _volume_sort_key(book: CollectionBook) -> tuple:
    volume = book.saga.volume if book.saga else None
    date = book.published_date or ""
    return (
        volume is None,
        volume or 0,
        0 if date else 1,
        date,
        normalize_text(book.title),
    )


def group_by_saga(books: list[CollectionBook]) -> list[SagaGroup]:
    by_saga: dict[int | str, list[CollectionBook]] = {}
    without_saga: list[CollectionBook] = []
    for book in books:
        if book.saga is None:
            without_saga.append(book)
            continue
        key = (
            book.saga.saga_id
            if book.saga.saga_id is not None
            else book.saga.normalized_name
        )
        by_saga.setdefault(key, []).append(book)

    groups = []
    for saga_books in by_saga.values():
        ordered = sorted(saga_books, key=_volume_sort_key)
        groups.append(SagaGroup(name=ordered[0].saga.name, books=ordered))
    groups.sort(key=lambda g: (normalize_text(g.name), g.name))

    if without_saga:
        groups.append(
            SagaGroup(name=None, books=sorted(without_saga, key=_author_sort_key))
        )
    return groups


def sort_books(
    books: list[CollectionBook], order: CollectionOrder
) -> list[CollectionBook]:
    if order is CollectionOrder.AUTHOR:
        return sorted(books, key=_author_sort_key)
    if order is CollectionOrder.SAGA:
        return [book for group in group_by_saga(books) for book in group.books]
    return books


class ListCollection:
    def __init__(self, collection_repository: CollectionRepository) -> None:
        self._collection_repository = collection_repository

    async def execute(
        self, order: CollectionOrder = CollectionOrder.DEFAULT
    ) -> list[CollectionBook]:
        books = await self._collection_repository.find_all()
        owned = [b for b in books if not b.is_to_buy]
        return sort_books(owned, order)
