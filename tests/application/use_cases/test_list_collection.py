from personal_library.application.use_cases.list_collection import (
    CollectionOrder,
    ListCollection,
)
from personal_library.domain.model.collection_book import CollectionBook
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
