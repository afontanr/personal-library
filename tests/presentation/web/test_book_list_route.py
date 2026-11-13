import re

import pytest
from httpx import ASGITransport, AsyncClient

from personal_library.domain.model.collection_book import CollectionBook
from personal_library.domain.model.saga import SagaMembership
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


async def test_book_list_excludes_to_buy_books():
    wanted = CollectionBook(
        isbn_13="9780000000009",
        title="Deseado",
        authors=["Ana"],
        added_at="2026-05-20T10:00:00",
        status="to_buy",
    )
    text = await _get("/", [BOOKS[0], wanted])

    assert "Deseado" not in text
    assert '<span class="book-count">1</span>' in text
    assert 'id="empty-state-template"' in text


def _saga_book(saga: SagaMembership) -> CollectionBook:
    return CollectionBook(
        isbn_13="9780000000003",
        title="Libro",
        authors=["Autor"],
        added_at="2026-05-10T10:00:00",
        saga=saga,
    )


async def test_card_shows_saga_and_volume():
    text = await _get("/", [_saga_book(SagaMembership("El Señor de los Anillos", 2.0))])

    assert "El Señor de los Anillos · 2</p>" in text


async def test_card_shows_saga_without_volume():
    text = await _get("/", [_saga_book(SagaMembership("Dune"))])

    assert 'class="book-card__saga">Dune</p>' in text


async def test_card_shows_volume_zero():
    text = await _get("/", [_saga_book(SagaMembership("Dune", 0.0))])

    assert "Dune · 0</p>" in text


async def test_card_without_saga_has_no_saga_line():
    text = await _get("/", BOOKS)

    assert "book-card__saga" not in text


# ─── Orden por saga ───

SAGA_BOOKS = [
    CollectionBook(
        isbn_13="9780000000011",
        title="Las dos torres",
        authors=["J. R. R. Tolkien"],
        added_at="2026-05-11T10:00:00",
        saga=SagaMembership("El Señor de los Anillos", 2, saga_id=1),
    ),
    CollectionBook(
        isbn_13="9780000000012",
        title="La comunidad del anillo",
        authors=["J. R. R. Tolkien"],
        added_at="2026-05-12T10:00:00",
        saga=SagaMembership("El Señor de los Anillos", 1, saga_id=1),
    ),
    CollectionBook(
        isbn_13="9780000000013",
        title="Dune",
        authors=["Frank Herbert"],
        added_at="2026-05-13T10:00:00",
        saga=SagaMembership("Dune", None, saga_id=2),
    ),
    *BOOKS,
]


async def test_book_list_toggle_offers_saga():
    text = await _get("/", BOOKS)

    assert '/?orden=saga"' in text
    assert not _active("Saga").search(text)


async def test_book_list_orden_saga_groups_books():
    text = await _get("/?orden=saga", SAGA_BOOKS)

    assert _active("Saga").search(text)
    assert not _active("Recientes").search(text)
    assert text.count('class="saga-group"') == 3
    assert (
        text.index("Dune · ")
        < text.index("El Señor de los Anillos · ")
        < text.index("Sin saga")
    )
    assert (
        'El Señor de los Anillos · <span class="saga-group__count">2</span> '
        '<span class="saga-group__noun">libros</span>'
    ) in text
    assert (
        'Dune · <span class="saga-group__count">1</span> '
        '<span class="saga-group__noun">libro</span>'
    ) in text
    assert text.index("La comunidad del anillo") < text.index("Las dos torres")
    assert text.index("Las dos torres") < text.index("Alfa") < text.index("Zeta")
    assert '<span class="book-count">5</span>' in text


async def test_book_list_orden_saga_card_shows_volume():
    grouped = await _get("/?orden=saga", SAGA_BOOKS)
    by_author = await _get("/?orden=autor", SAGA_BOOKS)

    assert '<p class="book-card__saga">Tomo 2</p>' in grouped
    assert '<p class="book-card__saga">El Señor de los Anillos' not in grouped
    # Dune has no volume: no saga line on its card.
    assert grouped.count('class="book-card__saga"') == 2
    assert '<p class="book-card__saga">El Señor de los Anillos · 2</p>' in by_author


async def test_book_list_orden_saga_without_sagas_has_no_headers():
    text = await _get("/?orden=saga", BOOKS)

    assert "saga-group" not in text
    assert "Sin saga" not in text
    assert 'class="book-grid"' in text
    assert text.index("Alfa") < text.index("Zeta")
    assert _active("Saga").search(text)


async def test_book_list_orden_saga_nests_card_headings_under_group():
    grouped = await _get("/?orden=saga", SAGA_BOOKS)
    flat = await _get("/?orden=autor", SAGA_BOOKS)

    assert '<h2 class="saga-group__title">' in grouped
    assert grouped.count('<h3 class="book-card__title">') == len(SAGA_BOOKS)
    assert '<h2 class="book-card__title">' not in grouped
    assert flat.count('<h2 class="book-card__title">') == len(SAGA_BOOKS)


async def test_book_list_orden_saga_marks_group_without_saga():
    text = await _get("/?orden=saga", SAGA_BOOKS)

    assert text.count("data-without-saga") == 1
    assert text.index("data-without-saga") > text.index("El Señor de los Anillos · ")
