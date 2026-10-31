import re

import pytest
from httpx import ASGITransport, AsyncClient

from personal_library.domain.model.collection_book import CollectionBook
from personal_library.domain.ports.collection_repository import CollectionRepository
from personal_library.main import create_app
from personal_library.presentation.api.dependencies import get_collection_repository


class FakeCollectionRepository(CollectionRepository):
    def __init__(self, books: list[CollectionBook] | None = None):
        self._books: dict[str, CollectionBook] = {b.isbn_13: b for b in books or []}

    async def save(self, book: CollectionBook) -> None:
        self._books[book.isbn_13] = book

    async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
        return self._books.get(isbn_13)

    async def find_all(self) -> list[CollectionBook]:
        return sorted(self._books.values(), key=lambda b: b.added_at, reverse=True)

    async def delete(self, isbn_13: str) -> None:
        self._books.pop(isbn_13, None)


BOOKS = [
    CollectionBook(
        isbn_13="9780000000001",
        title="Alfa",
        authors=["Isabel Allende"],
        added_at="2026-05-10T10:00:00",
    ),
    CollectionBook(
        isbn_13="9780000000002",
        title="Zeta",
        authors=["Jorge Luis Borges"],
        added_at="2026-05-15T16:00:00",
    ),
]


def _active(label: str) -> re.Pattern:
    return re.compile(rf'<a[^>]*aria-current="true"[^>]*>\s*{label}\s*</a>')


async def _get(path: str, books: list[CollectionBook]) -> str:
    app = create_app()
    fake_repo = FakeCollectionRepository(books)
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(path)

    assert response.status_code == 200
    return response.text


async def test_book_list_default_order_and_toggle():
    text = await _get("/", BOOKS)

    assert text.index("Zeta") < text.index("Alfa")
    assert 'class="sort-toggle"' in text
    assert '/?orden=autor"' in text
    assert _active("Recientes").search(text)
    assert not _active("Autor").search(text)


async def test_book_list_orden_autor():
    text = await _get("/?orden=autor", BOOKS)

    assert text.index("Alfa") < text.index("Zeta")
    assert _active("Autor").search(text)
    assert not _active("Recientes").search(text)


@pytest.mark.parametrize("path", ["/?orden=xyz", "/?orden="])
async def test_book_list_unknown_orden_falls_back_to_default(path):
    text = await _get(path, BOOKS)

    assert text.index("Zeta") < text.index("Alfa")
    assert _active("Recientes").search(text)


async def test_book_list_empty_collection_hides_toggle():
    text = await _get("/", [])

    assert "sort-toggle" not in text
