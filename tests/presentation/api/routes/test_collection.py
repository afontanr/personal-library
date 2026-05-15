import pytest
from httpx import ASGITransport, AsyncClient

from personal_library.domain.model.collection_book import (
    CollectionBook,
    ReadingPeriod,
)
from personal_library.domain.ports.collection_repository import CollectionRepository
from personal_library.main import create_app
from personal_library.presentation.api.dependencies import (
    get_collection_repository,
)


class FakeCollectionRepository(CollectionRepository):
    def __init__(self):
        self._books: dict[str, CollectionBook] = {}

    async def save(self, book: CollectionBook) -> None:
        self._books[book.isbn_13] = book

    async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
        return self._books.get(isbn_13)

    async def find_all(self) -> list[CollectionBook]:
        return sorted(
            self._books.values(),
            key=lambda b: b.added_at,
            reverse=True,
        )


@pytest.mark.asyncio
async def test_save_book_returns_201():
    fake_repo = FakeCollectionRepository()
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/collection",
            json={
                "isbn_13": "9788466341172",
                "isbn_10": "846634117X",
                "title": "Medio Mundo",
                "authors": ["Joe Abercrombie"],
                "description": "Una novela.",
                "published_date": "2026-05-19",
                "cover_image_url": "https://example.com/cover.jpg",
                "status": "new",
                "rating": 4.0,
                "tags": ["fantasy"],
                "opinion": "Buenisimo.",
                "reading_periods": [
                    {"start_date": "2026-05-10", "end_date": "2026-05-15"},
                ],
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["isbn_13"] == "9788466341172"
    assert data["isbn_10"] == "846634117X"
    assert data["title"] == "Medio Mundo"
    assert data["authors"] == ["Joe Abercrombie"]
    assert data["description"] == "Una novela."
    assert data["published_date"] == "2026-05-19"
    assert data["cover_image_url"] == "https://example.com/cover.jpg"
    assert data["status"] == "new"
    assert data["rating"] == 4.0
    assert data["tags"] == ["fantasy"]
    assert data["opinion"] == "Buenisimo."
    assert "added_at" in data
    assert len(data["reading_periods"]) == 1
    assert data["reading_periods"][0]["start_date"] == "2026-05-10"
    assert data["reading_periods"][0]["end_date"] == "2026-05-15"


@pytest.mark.asyncio
async def test_save_book_minimal_fields():
    fake_repo = FakeCollectionRepository()
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/collection",
            json={
                "isbn_13": "9788466341172",
                "title": "Medio Mundo",
                "authors": ["Joe Abercrombie"],
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "new"
    assert data["rating"] is None
    assert data["tags"] == []
    assert data["opinion"] is None
    assert data["reading_periods"] == []


@pytest.mark.asyncio
async def test_list_collection_returns_books_ordered():
    fake_repo = FakeCollectionRepository()
    book1 = CollectionBook(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-10T10:00:00",
    )
    book2 = CollectionBook(
        isbn_13="9780451524935",
        isbn_10="0451524934",
        title="1984",
        authors=["George Orwell"],
        added_at="2026-05-15T16:00:00",
    )
    fake_repo._books["9788466341172"] = book1
    fake_repo._books["9780451524935"] = book2

    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/collection")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["isbn_13"] == "9780451524935"  # most recent first
    assert data[1]["isbn_13"] == "9788466341172"


@pytest.mark.asyncio
async def test_list_collection_returns_empty_array():
    fake_repo = FakeCollectionRepository()
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/collection")

    assert response.status_code == 200
    assert response.json() == []
