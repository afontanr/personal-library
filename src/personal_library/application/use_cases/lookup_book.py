from personal_library.domain.model.book import BookInfo
from personal_library.domain.ports.book_repository import BookRepository
from personal_library.domain.ports.cover_resolver import CoverResolver


def to_isbn13(isbn: str) -> str:
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
    def __init__(
        self,
        book_repository: BookRepository,
        cover_resolver: CoverResolver,
    ) -> None:
        self._book_repository = book_repository
        self._cover_resolver = cover_resolver

    async def execute(self, isbn: str) -> BookInfo:
        isbn_13 = to_isbn13(isbn)
        book = await self._book_repository.find_by_isbn(isbn_13)
        cover_url = await self._cover_resolver.resolve(isbn_13)
        if cover_url:
            book = BookInfo(
                isbn_13=book.isbn_13,
                isbn_10=book.isbn_10,
                title=book.title,
                authors=book.authors,
                description=book.description,
                published_date=book.published_date,
                cover_image_url=cover_url,
            )
        return book


def to_isbn10(isbn_13: str) -> str | None:
    """Convert ISBN-13 to ISBN-10. Only works for ISBN-13 starting with 978."""
    if not isbn_13.startswith("978") or len(isbn_13) != 13:
        return None
    digits = isbn_13[3:12]
    total = sum(int(d) * (10 - i) for i, d in enumerate(digits))
    check = (11 - (total % 11)) % 11
    check_char = "X" if check == 10 else str(check)
    return digits + check_char
