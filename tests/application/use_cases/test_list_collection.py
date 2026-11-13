from personal_library.application.use_cases.list_collection import (
    CollectionOrder,
    ListCollection,
    group_by_saga,
)
from personal_library.domain.model.collection_book import CollectionBook
from personal_library.domain.model.saga import SagaMembership
from personal_library.domain.ports.collection_repository import CollectionRepository


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


def _books(*specs: tuple) -> list[CollectionBook]:
    """Build books from (title, authors, published_date) tuples.

    Later specs get more recent added_at values.
    """
    return [
        CollectionBook(
            isbn_13=f"978000000{i:04d}",
            title=title,
            authors=authors,
            published_date=published_date,
            added_at=f"2026-01-01T00:00:{i:02d}",
        )
        for i, (title, authors, published_date) in enumerate(specs)
    ]


async def _titles(books: list[CollectionBook], order: CollectionOrder) -> list[str]:
    use_case = ListCollection(collection_repository=FakeCollectionRepository(books))
    return [b.title for b in await use_case.execute(order)]


def test_from_param():
    assert CollectionOrder.from_param("autor") is CollectionOrder.AUTHOR
    assert CollectionOrder.from_param("saga") is CollectionOrder.SAGA
    for raw in (None, "", "xyz", "defecto"):
        assert CollectionOrder.from_param(raw) is CollectionOrder.DEFAULT


async def test_default_order_keeps_repository_order():
    books = _books(
        ("Primero", ["Zoe"], None),
        ("Segundo", ["Ana"], None),
        ("Tercero", ["Marta"], None),
    )

    assert await _titles(books, CollectionOrder.DEFAULT) == [
        "Tercero",
        "Segundo",
        "Primero",
    ]


async def test_execute_defaults_to_default_order():
    books = _books(("Viejo", ["Ana"], None), ("Nuevo", ["Zoe"], None))
    use_case = ListCollection(collection_repository=FakeCollectionRepository(books))

    assert [b.title for b in await use_case.execute()] == ["Nuevo", "Viejo"]


async def test_author_order_sorts_by_first_author_as_written():
    books = _books(
        ("Ficciones", ["Jorge Luis Borges"], None),
        ("Cien años de soledad", ["Gabriel García Márquez"], None),
        ("La casa de los espíritus", ["Isabel Allende"], None),
    )

    assert await _titles(books, CollectionOrder.AUTHOR) == [
        "Cien años de soledad",
        "La casa de los espíritus",
        "Ficciones",
    ]


async def test_author_order_uses_only_first_author():
    books = _books(
        ("Good Omens", ["Terry Pratchett", "Neil Gaiman"], None),
        ("It", ["Stephen King"], None),
    )

    assert await _titles(books, CollectionOrder.AUTHOR) == ["It", "Good Omens"]


async def test_author_order_ignores_accents_and_case():
    books = _books(
        ("Ficciones", ["Borges"], None),
        ("Poemas", ["Ángel González"], None),
        ("La lengua de las mariposas", ["Alberto Méndez"], None),
        ("All About Love", ["bell hooks"], None),
    )

    assert await _titles(books, CollectionOrder.AUTHOR) == [
        "La lengua de las mariposas",
        "Poemas",
        "All About Love",
        "Ficciones",
    ]


async def test_same_author_sorted_by_published_date_then_undated_then_title():
    books = _books(
        ("B", ["Autor"], "1999"),
        ("A", ["Autor"], None),
        ("C", ["Autor"], "1998-05-12"),
        ("D", ["Autor"], None),
    )

    assert await _titles(books, CollectionOrder.AUTHOR) == ["C", "B", "A", "D"]


async def test_books_without_author_go_last_sorted_by_title():
    books = _books(
        ("Zeta", [], None),
        ("Alfa", ["  "], None),
        ("Beta", ["", "X"], None),
        ("Ficciones", ["Borges"], None),
    )

    assert await _titles(books, CollectionOrder.AUTHOR) == [
        "Ficciones",
        "Alfa",
        "Beta",
        "Zeta",
    ]


async def test_excludes_to_buy_books():
    books = [
        CollectionBook(
            isbn_13="9780000000001",
            title="Mío",
            authors=["Ana"],
            added_at="2026-01-01T00:00:01",
        ),
        CollectionBook(
            isbn_13="9780000000002",
            title="Deseado",
            authors=["Zoe"],
            added_at="2026-01-01T00:00:02",
            status="to_buy",
        ),
    ]

    for order in CollectionOrder:
        assert await _titles(books, order) == ["Mío"]


# ─── Orden por saga ───


def _saga_books(*specs: tuple) -> list[CollectionBook]:
    """Build books from (title, saga, published_date[, authors]) tuples.

    ``saga`` is a SagaMembership or None.
    """
    return [
        CollectionBook(
            isbn_13=f"978000001{i:04d}",
            title=spec[0],
            authors=spec[3] if len(spec) > 3 else ["Autor"],
            published_date=spec[2],
            added_at=f"2026-01-01T00:00:{i:02d}",
            saga=spec[1],
        )
        for i, spec in enumerate(specs)
    ]


def _groups(books: list[CollectionBook]) -> list[tuple[str | None, list[str]]]:
    return [(g.name, [b.title for b in g.books]) for g in group_by_saga(books)]


def test_group_by_saga_orders_sagas_by_normalized_name():
    books = _saga_books(
        ("F1", SagaMembership("fundación", 1, saga_id=1), None),
        ("E1", SagaMembership("Éxodo", 1, saga_id=2), None),
        ("D1", SagaMembership("Dune", 1, saga_id=3), None),
    )

    assert [name for name, _ in _groups(books)] == ["Dune", "Éxodo", "fundación"]


def test_group_by_saga_orders_by_volume_then_date_then_title():
    def saga(volume):
        return SagaMembership("Saga", volume, saga_id=1)

    books = _saga_books(
        ("Sin tomo", saga(None), None),
        ("Tomo 3.5 nuevo", saga(3.5), "1990"),
        ("Tomo 1", saga(1), None),
        ("Precuela", saga(0), None),
        ("Tomo 3.5 viejo", saga(3.5), "1985"),
    )

    assert _groups(books) == [
        (
            "Saga",
            ["Precuela", "Tomo 1", "Tomo 3.5 viejo", "Tomo 3.5 nuevo", "Sin tomo"],
        )
    ]


def test_group_by_saga_merges_same_saga_id():
    books = _saga_books(
        ("Dos", SagaMembership("el señor", 2, saga_id=1), None),
        ("Uno", SagaMembership("El Señor", 1, saga_id=1), None),
    )

    assert _groups(books) == [("El Señor", ["Uno", "Dos"])]


def test_group_by_saga_falls_back_to_normalized_name_without_id():
    books = _saga_books(
        ("Uno", SagaMembership("Dune", 1), None),
        ("Dos", SagaMembership(" dune ", 2), None),
    )

    assert _groups(books) == [("Dune", ["Uno", "Dos"])]


def test_group_by_saga_puts_books_without_saga_last_by_author():
    books = _saga_books(
        ("De Zoe", None, None, ["Zoe"]),
        ("Saga 1", SagaMembership("Zzz", 1, saga_id=1), None),
        ("De Ana", None, None, ["Ana"]),
    )

    assert _groups(books) == [("Zzz", ["Saga 1"]), (None, ["De Ana", "De Zoe"])]


def test_group_by_saga_single_book_saga_is_a_group():
    books = _saga_books(("Solo", SagaMembership("Única", None, saga_id=1), None))

    assert _groups(books) == [("Única", ["Solo"])]


def test_group_by_saga_only_no_saga_books():
    books = _saga_books(("B", None, None, ["Zoe"]), ("A", None, None, ["Ana"]))

    assert _groups(books) == [(None, ["A", "B"])]


def test_group_by_saga_empty():
    assert group_by_saga([]) == []


async def test_saga_order_flattens_groups():
    books = _saga_books(
        ("Suelto", None, None),
        ("B2", SagaMembership("B", 2, saga_id=2), None),
        ("A1", SagaMembership("A", 1, saga_id=1), None),
        ("B1", SagaMembership("B", 1, saga_id=2), None),
    )

    assert await _titles(books, CollectionOrder.SAGA) == ["A1", "B1", "B2", "Suelto"]
