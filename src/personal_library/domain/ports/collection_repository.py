from abc import ABC, abstractmethod

from personal_library.domain.model.collection_book import CollectionBook


class CollectionRepository(ABC):
    @abstractmethod
    async def save(self, book: CollectionBook) -> None:
        """Persist a book to the collection."""

    @abstractmethod
    async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
        """Find a book by ISBN-13, or None if not in collection."""

    @abstractmethod
    async def find_all(self) -> list[CollectionBook]:
        """Return all books in the collection, ordered by added_at DESC."""
