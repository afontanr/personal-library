import pytest

from personal_library.application.use_cases.lookup_book import (
    LookupBookByIsbn,
    _to_isbn13,
)
from personal_library.domain.exceptions import BookNotFoundError
from personal_library.domain.model.book import BookInfo
from personal_library.domain.ports.book_repository import BookRepository


class FakeBookRepository(BookRepository):
    def __init__(self, result: BookInfo | None = None):
        self._result = result

    async def find_by_isbn(self, isbn_13: str) -> BookInfo:
        if self._result is None:
            raise BookNotFoundError(isbn_13)
        return self._result


@pytest.mark.asyncio
async def test_lookup_returns_book_when_found():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description="Desc",
        published_date="2026-05-19",
        cover_image_url="https://images-na.ssl-images-amazon.com/images/P/846634117X.jpg",
    )
    repo = FakeBookRepository(result=book)
    use_case = LookupBookByIsbn(book_repository=repo)

    result = await use_case.execute("9788466341172")

    assert result == book


@pytest.mark.asyncio
async def test_lookup_raises_not_found_when_missing():
    repo = FakeBookRepository(result=None)
    use_case = LookupBookByIsbn(book_repository=repo)

    with pytest.raises(BookNotFoundError):
        await use_case.execute("0000000000000")


def test_to_isbn13_returns_isbn13_unchanged():
    assert _to_isbn13("9788466341172") == "9788466341172"


def test_to_isbn13_converts_isbn10():
    # ISBN-10 "846634117X" → ISBN-13 "9788466341172"
    assert _to_isbn13("846634117X") == "9788466341172"


@pytest.mark.asyncio
async def test_lookup_normalises_isbn10_to_isbn13():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description=None,
        published_date=None,
        cover_image_url=None,
    )
    repo = FakeBookRepository(result=book)
    use_case = LookupBookByIsbn(book_repository=repo)

    result = await use_case.execute("846634117X")

    assert result.isbn_13 == "9788466341172"
