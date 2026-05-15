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
        return list(self._books.values())


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
