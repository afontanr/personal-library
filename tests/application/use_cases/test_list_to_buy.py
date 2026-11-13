from personal_library.application.use_cases.list_collection import CollectionOrder
from personal_library.application.use_cases.list_to_buy import ListToBuy
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


def _book(i: int, title: str, status: str, authors: list[str] | None = None):
    return CollectionBook(
        isbn_13=f"978000000{i:04d}",
        title=title,
        authors=authors or ["Autor"],
        added_at=f"2026-01-01T00:00:{i:02d}",
        status=status,
    )


async def _titles(
    books: list[CollectionBook], order: CollectionOrder = CollectionOrder.DEFAULT
) -> list[str]:
    use_case = ListToBuy(collection_repository=FakeCollectionRepository(books))
    return [b.title for b in await use_case.execute(order)]


async def test_returns_only_to_buy_books_newest_first():
    books = [
        _book(1, "Uno", "to_buy"),
        _book(2, "Leído", "read"),
        _book(3, "Dos", "to_buy"),
        _book(4, "Tres", "to_buy"),
    ]

    assert await _titles(books) == ["Tres", "Dos", "Uno"]


async def test_author_order():
    books = [
        _book(1, "La casa de los espíritus", "to_buy", ["Isabel Allende"]),
        _book(2, "Ficciones", "to_buy", ["Jorge Luis Borges"]),
    ]

    assert await _titles(books, CollectionOrder.AUTHOR) == [
        "La casa de los espíritus",
        "Ficciones",
    ]


async def test_empty_when_no_to_buy_books():
    books = [_book(1, "Mío", "new"), _book(2, "Otro", "new")]

    assert await _titles(books) == []


async def test_saga_order_falls_back_to_default():
    books = [
        _book(1, "B", "to_buy", ["Zoe"]),
        _book(2, "A", "to_buy", ["Ana"]),
    ]

    assert await _titles(books, CollectionOrder.SAGA) == await _titles(books)
