from httpx import ASGITransport, AsyncClient

from personal_library.domain.model.book import BookInfo
from personal_library.domain.model.collection_book import CollectionBook
from personal_library.domain.model.saga import SagaMembership
from personal_library.domain.ports.collection_repository import CollectionRepository
from personal_library.main import create_app
from personal_library.presentation.api.dependencies import (
    get_collection_repository,
    get_lookup_book_use_case,
)


class FakeCollectionRepository(CollectionRepository):
    def __init__(self, books: list[CollectionBook]):
        self._books = {b.isbn_13: b for b in books}

    async def save(self, book: CollectionBook) -> None:
        self._books[book.isbn_13] = book

    async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
        return self._books.get(isbn_13)

    async def find_all(self) -> list[CollectionBook]:
        return list(self._books.values())

    async def delete(self, isbn_13: str) -> None:
        self._books.pop(isbn_13, None)


async def test_detail_renders_saga_section_and_preloads_saga():
    book = CollectionBook(
        isbn_13="9780000000001",
        title="Dune",
        authors=["Frank Herbert"],
        added_at="2026-05-10T10:00:00",
        saga=SagaMembership("Dune", 1.0, saga_id=3),
    )
    app = create_app()
    fake_repo = FakeCollectionRepository([book])
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo
    app.dependency_overrides[get_lookup_book_use_case] = lambda: None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/book/9780000000001")

    assert response.status_code == 200
    assert 'id="saga-section"' in response.text
    assert '"name": "Dune"' in response.text
    assert '"volume": 1.0' in response.text


class FakeLookup:
    async def execute(self, isbn: str) -> BookInfo:
        return BookInfo(
            isbn_13="9780000000009",
            isbn_10=None,
            title="Nuevo",
            authors=["Autor"],
            description=None,
            published_date=None,
            cover_image_url=None,
        )


async def test_detail_of_book_not_in_collection_clears_stale_saga():
    app = create_app()
    fake_repo = FakeCollectionRepository([])
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo
    app.dependency_overrides[get_lookup_book_use_case] = FakeLookup

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/book/9780000000009")

    assert response.status_code == 200
    assert "localStorage.removeItem('pl_' + isbn + '_saga');" in response.text
