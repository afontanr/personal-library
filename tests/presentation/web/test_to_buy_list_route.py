import re

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


DESEADO = CollectionBook(
    isbn_13="9780000000001",
    title="Deseado",
    authors=["Isabel Allende"],
    added_at="2026-05-10T10:00:00",
    status="to_buy",
)
OTRO = CollectionBook(
    isbn_13="9780000000002",
    title="Otro",
    authors=["Jorge Luis Borges"],
    added_at="2026-05-15T16:00:00",
    status="to_buy",
)
MIO = CollectionBook(
    isbn_13="9780000000003",
    title="Mío",
    authors=["Ana"],
    added_at="2026-05-20T10:00:00",
)
BOOKS = [DESEADO, OTRO, MIO]


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


async def test_to_buy_list_shows_only_to_buy_books():
    text = await _get("/futuras-compras", BOOKS)

    assert "Deseado" in text
    assert "Otro" in text
    assert "Mío" not in text
    assert '<span class="book-count">2</span>' in text
    assert "libros por comprar" in text
    assert 'id="empty-state-template"' in text


async def test_to_buy_list_order_toggle():
    default = await _get("/futuras-compras", BOOKS)
    by_author = await _get("/futuras-compras?orden=autor", BOOKS)

    assert default.index("Otro") < default.index("Deseado")
    assert _active("Recientes").search(default)
    assert '/futuras-compras?orden=autor"' in default
    assert by_author.index("Deseado") < by_author.index("Otro")
    assert _active("Autor").search(by_author)


async def test_to_buy_list_empty_state():
    text = await _get("/futuras-compras", [MIO])

    assert "No tienes futuras compras" in text
    assert 'class="sort-toggle"' not in text


async def test_nav_links_to_to_buy():
    text = await _get("/", [])

    assert re.search(r'<a href="[^"]*/futuras-compras">Futuras compras</a>', text)
    assert "Futuras compras" in text
