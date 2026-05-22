import pytest

from personal_library.application.use_cases.lookup_book import (
    LookupBookByIsbn,
    to_isbn10,
    to_isbn13,
)
from personal_library.domain.exceptions import BookNotFoundError
from personal_library.domain.model.book import BookInfo
from personal_library.domain.ports.book_repository import BookRepository
from personal_library.domain.ports.cover_resolver import CoverResolver


class FakeBookRepository(BookRepository):
    def __init__(self, result: BookInfo | None = None):
        self._result = result

    async def find_by_isbn(self, isbn_13: str) -> BookInfo:
        if self._result is None:
            raise BookNotFoundError(isbn_13)
        return self._result


class FakeCoverResolver(CoverResolver):
    def __init__(self, url: str | None = None):
        self._url = url

    async def resolve(self, isbn_13: str) -> str | None:
        return self._url


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
    resolver = FakeCoverResolver(url=None)
    use_case = LookupBookByIsbn(book_repository=repo, cover_resolver=resolver)

    result = await use_case.execute("9788466341172")

    assert result == book


@pytest.mark.asyncio
async def test_lookup_raises_not_found_when_missing():
    repo = FakeBookRepository(result=None)
    resolver = FakeCoverResolver(url=None)
    use_case = LookupBookByIsbn(book_repository=repo, cover_resolver=resolver)

    with pytest.raises(BookNotFoundError):
        await use_case.execute("0000000000000")


def test_to_isbn13_returns_isbn13_unchanged():
    assert to_isbn13("9788466341172") == "9788466341172"


def test_to_isbn13_converts_isbn10():
    # ISBN-10 "846634117X" → ISBN-13 "9788466341172"
    assert to_isbn13("846634117X") == "9788466341172"


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
    resolver = FakeCoverResolver(url=None)
    use_case = LookupBookByIsbn(book_repository=repo, cover_resolver=resolver)

    result = await use_case.execute("846634117X")

    assert result.isbn_13 == "9788466341172"


def test_to_isbn10_from_isbn13_with_978_prefix():
    # ISBN-13 "9788466341172" → ISBN-10 "846634117X"
    assert to_isbn10("9788466341172") == "846634117X"


def test_to_isbn10_from_isbn13_with_979_prefix():
    # ISBN-13 "9791090636071" → ISBN-10 check digit is different
    # 979 is not a valid ISBN-10 prefix, returns original
    result = to_isbn10("9791090636071")
    assert result is None


def test_to_isbn10_short_code_checksum_10():
    # ISBN-13 "9780306406157" → ISBN-10 "0306406152" (checkdigit 2, not X)
    assert to_isbn10("9780306406157") == "0306406152"


@pytest.mark.asyncio
async def test_lookup_replaces_cover_when_resolved():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description="Desc",
        published_date="2026-05-19",
        cover_image_url="https://original-cover.jpg",
    )
    repo = FakeBookRepository(result=book)
    resolver = FakeCoverResolver(url="https://resolved-cover.jpg")
    use_case = LookupBookByIsbn(book_repository=repo, cover_resolver=resolver)

    result = await use_case.execute("9788466341172")

    assert result.cover_image_url == "https://resolved-cover.jpg"
    assert result.title == "Medio Mundo"


@pytest.mark.asyncio
async def test_lookup_keeps_original_cover_when_resolver_returns_none():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description="Desc",
        published_date="2026-05-19",
        cover_image_url="https://original-cover.jpg",
    )
    repo = FakeBookRepository(result=book)
    resolver = FakeCoverResolver(url=None)
    use_case = LookupBookByIsbn(book_repository=repo, cover_resolver=resolver)

    result = await use_case.execute("9788466341172")

    assert result.cover_image_url == "https://original-cover.jpg"


@pytest.mark.asyncio
async def test_lookup_passes_isbn13_to_resolver():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description=None,
        published_date=None,
        cover_image_url=None,
    )

    class SpyCoverResolver(CoverResolver):
        def __init__(self):
            self.called_with: str | None = None

        async def resolve(self, isbn_13: str) -> str | None:
            self.called_with = isbn_13
            return None

    repo = FakeBookRepository(result=book)
    resolver = SpyCoverResolver()
    use_case = LookupBookByIsbn(book_repository=repo, cover_resolver=resolver)

    await use_case.execute("846634117X")

    assert resolver.called_with == "9788466341172"


@pytest.mark.asyncio
async def test_lookup_survives_resolver_failure():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description=None,
        published_date=None,
        cover_image_url="https://original-cover.jpg",
    )

    class RaisingCoverResolver(CoverResolver):
        async def resolve(self, isbn_13: str) -> str | None:
            raise RuntimeError("service down")

    repo = FakeBookRepository(result=book)
    resolver = RaisingCoverResolver()
    use_case = LookupBookByIsbn(book_repository=repo, cover_resolver=resolver)

    result = await use_case.execute("9788466341172")

    assert result == book
