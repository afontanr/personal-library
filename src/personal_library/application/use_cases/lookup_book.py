from personal_library.domain.model.book import BookInfo
from personal_library.domain.ports.book_repository import BookRepository


class LookupBookByIsbn:
    def __init__(self, book_repository: BookRepository) -> None:
        self._book_repository = book_repository

    async def execute(self, isbn_13: str) -> BookInfo | None:
        return await self._book_repository.find_by_isbn(isbn_13)
