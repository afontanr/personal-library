from abc import ABC, abstractmethod

from personal_library.domain.model.book import BookInfo


class BookRepository(ABC):
    @abstractmethod
    async def find_by_isbn(self, isbn_13: str) -> BookInfo:
        """Fetch book info for the given ISBN-13.

        Raises BookNotFoundError if not found.
        """
