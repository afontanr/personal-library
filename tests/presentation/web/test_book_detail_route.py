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


class FakeLookup:
    async def execute(self, isbn: str) -> BookInfo:
        return BookInfo(
            isbn_13=isbn,
            isbn_10=None,
            title="Sin guardar",
            authors=["Ana"],
            description=None,
            published_date=None,
            cover_image_url=None,
        )


ISBN = "9788466341172"


def _book(status: str) -> CollectionBook:
    return CollectionBook(
        isbn_13=ISBN,
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-10T10:00:00",
        status=status,
    )


async def _get(books: list[CollectionBook]) -> str:
    app = create_app()
    fake_repo = FakeCollectionRepository(books)
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo
    app.dependency_overrides[get_lookup_book_use_case] = lambda: FakeLookup()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/book/{ISBN}")

    assert response.status_code == 200
    return response.text


async def test_to_buy_book_detail():
    text = await _get([_book("to_buy")])

    assert "En futuras compras" in text
    assert 'id="purchase-book-btn"' in text
    assert 'value="to_buy" selected' in text
    assert "Por comprar" in text
    assert 'data-return-url="/futuras-compras"' in text
    assert 'data-list-label="tus futuras compras"' in text
    assert 'data-to-buy="true"' in text
    assert 'id="rating-section"' not in text
    assert 'id="opinion-section"' not in text
    assert 'id="reading-dates-section"' not in text
    assert "En tu colección" not in text


async def test_collection_book_detail():
    text = await _get([_book("read")])

    assert "En tu colección" in text
    assert 'id="rating-section"' in text
    assert 'data-return-url="/"' in text
    assert 'data-list-label="tu coleccion"' in text
    assert 'data-to-buy="false"' in text
    assert 'id="purchase-book-btn"' not in text


async def test_unsaved_book_detail_offers_both_actions():
    text = await _get([])

    assert "Añadir a mi colección" in text
    assert 'id="save-to-buy-btn"' in text
    assert "Añadir a futuras compras" in text
    assert 'data-to-buy="false"' in text


async def test_detail_renders_saga_section_and_preloads_saga():
    book = CollectionBook(
        isbn_13=ISBN,
        title="Dune",
        authors=["Frank Herbert"],
        added_at="2026-05-10T10:00:00",
        saga=SagaMembership("Dune", 1.0, saga_id=3),
    )
    text = await _get([book])

    assert 'id="saga-section"' in text
    assert '"name": "Dune"' in text
    assert '"volume": 1.0' in text


async def test_detail_of_book_not_in_collection_clears_stale_saga():
    text = await _get([])

    assert "localStorage.removeItem('pl_' + isbn + '_saga');" in text
