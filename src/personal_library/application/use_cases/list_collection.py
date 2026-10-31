import unicodedata
from enum import StrEnum

from personal_library.domain.model.collection_book import CollectionBook
from personal_library.domain.ports.collection_repository import CollectionRepository


class CollectionOrder(StrEnum):
    DEFAULT = "defecto"
    AUTHOR = "autor"

    @classmethod
    def from_param(cls, value: str | None) -> "CollectionOrder":
        return cls.AUTHOR if value == cls.AUTHOR.value else cls.DEFAULT


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold().strip()


def _author_sort_key(book: CollectionBook) -> tuple:
    author = _normalize(book.authors[0]) if book.authors else ""
    title = _normalize(book.title)
    if not author:
        return (1, "", 0, "", title)
    date = book.published_date or ""
    return (0, author, 0 if date else 1, date, title)


class ListCollection:
    def __init__(self, collection_repository: CollectionRepository) -> None:
        self._collection_repository = collection_repository

    async def execute(
        self, order: CollectionOrder = CollectionOrder.DEFAULT
    ) -> list[CollectionBook]:
        books = await self._collection_repository.find_all()
        if order is CollectionOrder.AUTHOR:
            return sorted(books, key=_author_sort_key)
        return books
