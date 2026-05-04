from personal_library.domain.model.book import BookInfo
from personal_library.domain.ports.book_repository import BookRepository


def _to_isbn13(isbn: str) -> str:
    """Convert ISBN-10 to ISBN-13. Return ISBN-13 unchanged."""
    if len(isbn) == 13:
        return isbn
    # Prefix with "978", drop the ISBN-10 check digit, recalculate for ISBN-13
    digits = "978" + isbn[:9]
    total = sum(
        int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits)
    )
    check = (10 - (total % 10)) % 10
    return digits + str(check)


class LookupBookByIsbn:
    def __init__(self, book_repository: BookRepository) -> None:
        self._book_repository = book_repository

    async def execute(self, isbn: str) -> BookInfo:
        isbn_13 = _to_isbn13(isbn)
        return await self._book_repository.find_by_isbn(isbn_13)
