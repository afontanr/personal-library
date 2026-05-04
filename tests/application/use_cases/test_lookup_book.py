import pytest

from personal_library.application.use_cases.lookup_book import LookupBookByIsbn
from personal_library.domain.model.book import BookInfo
from personal_library.domain.ports.book_repository import BookRepository


class FakeBookRepository(BookRepository):
    def __init__(self, result: BookInfo | None):
        self._result = result

    async def find_by_isbn(self, isbn_13: str) -> BookInfo | None:
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
async def test_lookup_returns_none_when_not_found():
    repo = FakeBookRepository(result=None)
    use_case = LookupBookByIsbn(book_repository=repo)

    result = await use_case.execute("0000000000000")

    assert result is None
