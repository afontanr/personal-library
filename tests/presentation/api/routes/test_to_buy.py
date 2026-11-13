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


ALLENDE = CollectionBook(
    isbn_13="9780000000001",
    title="La casa de los espíritus",
    authors=["Isabel Allende"],
    added_at="2026-05-10T10:00:00",
    status="to_buy",
)
BORGES = CollectionBook(
    isbn_13="9780000000002",
    title="Ficciones",
    authors=["Jorge Luis Borges"],
    added_at="2026-05-15T16:00:00",
    status="to_buy",
)
OWNED = CollectionBook(
    isbn_13="9780000000003",
    title="Mío",
    authors=["Ana"],
    added_at="2026-05-20T10:00:00",
)


async def _get(books: list[CollectionBook], params: dict | None = None):
    app = create_app()
    fake_repo = FakeCollectionRepository(books)
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/to-buy", params=params)

    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_list_to_buy_returns_only_to_buy_books():
    data = await _get([ALLENDE, OWNED])

    assert [b["isbn_13"] for b in data] == [ALLENDE.isbn_13]
    assert data[0]["status"] == "to_buy"


@pytest.mark.asyncio
async def test_list_to_buy_orden_autor():
    default = await _get([ALLENDE, BORGES])
    by_author = await _get([ALLENDE, BORGES], {"orden": "autor"})

    assert [b["authors"][0] for b in default] == [
        "Jorge Luis Borges",
        "Isabel Allende",
    ]
    assert [b["authors"][0] for b in by_author] == [
        "Isabel Allende",
        "Jorge Luis Borges",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("orden", ["xyz", ""])
async def test_list_to_buy_unknown_orden_falls_back_to_default(orden):
    data = await _get([ALLENDE, BORGES], {"orden": orden})

    assert [b["authors"][0] for b in data] == [
        "Jorge Luis Borges",
        "Isabel Allende",
    ]


@pytest.mark.asyncio
async def test_list_to_buy_returns_empty_array():
    assert await _get([OWNED]) == []


@pytest.mark.asyncio
async def test_list_to_buy_orden_saga_falls_back_to_default():
    data = await _get([ALLENDE, BORGES], {"orden": "saga"})

    assert [b["authors"][0] for b in data] == [
        "Jorge Luis Borges",
        "Isabel Allende",
    ]
