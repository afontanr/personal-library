import pytest
from httpx import ASGITransport, AsyncClient

from personal_library.domain.model.book import BookInfo
from personal_library.domain.ports.book_repository import BookRepository
from personal_library.main import create_app
from personal_library.presentation.api.dependencies import get_book_repository


class FakeBookRepository(BookRepository):
    def __init__(self, result: BookInfo | None):
        self._result = result

    async def find_by_isbn(self, isbn_13: str) -> BookInfo | None:
        return self._result


@pytest.mark.asyncio
async def test_get_book_returns_200():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description="Desc",
        published_date="2026-05-19",
        cover_image_url="https://images-na.ssl-images-amazon.com/images/P/846634117X.jpg",
    )
    fake_repo = FakeBookRepository(result=book)
    app = create_app()
    app.dependency_overrides[get_book_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/books/9788466341172")

    assert response.status_code == 200
    data = response.json()
    assert data["isbn_13"] == "9788466341172"
    assert data["isbn_10"] == "846634117X"
    assert data["title"] == "Medio Mundo"
    assert data["authors"] == ["Joe Abercrombie"]
    assert (
        data["cover_image_url"]
        == "https://images-na.ssl-images-amazon.com/images/P/846634117X.jpg"
    )


@pytest.mark.asyncio
async def test_get_book_returns_404_when_not_found():
    fake_repo = FakeBookRepository(result=None)
    app = create_app()
    app.dependency_overrides[get_book_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/books/0000000000000")

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"
