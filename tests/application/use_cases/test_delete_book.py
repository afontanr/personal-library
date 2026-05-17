import pytest

from personal_library.application.use_cases.delete_book import (
    DeleteBookFromCollection,
)
from personal_library.domain.exceptions import BookNotFoundError
from personal_library.domain.model.collection_book import (
    CollectionBook,
)
from personal_library.domain.ports.collection_repository import CollectionRepository


class FakeCollectionRepository(CollectionRepository):
    def __init__(self):
        self._books: dict[str, CollectionBook] = {}
        self.deleted: list[str] = []

    async def save(self, book: CollectionBook) -> None:
        self._books[book.isbn_13] = book

    async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
        return self._books.get(isbn_13)

    async def find_all(self) -> list[CollectionBook]:
        return list(self._books.values())

    async def delete(self, isbn_13: str) -> None:
        self._books.pop(isbn_13, None)
        self.deleted.append(isbn_13)


@pytest.mark.asyncio
async def test_delete_removes_book_from_collection():
    repo = FakeCollectionRepository()
    book = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-15T16:00:00",
    )
    await repo.save(book)
    use_case = DeleteBookFromCollection(collection_repository=repo)

    await use_case.execute("9788466341172")

    assert len(repo.deleted) == 1
    assert repo.deleted[0] == "9788466341172"
    assert await repo.find_by_isbn("9788466341172") is None


@pytest.mark.asyncio
async def test_delete_nonexistent_book_raises_error():
    repo = FakeCollectionRepository()
    use_case = DeleteBookFromCollection(collection_repository=repo)

    with pytest.raises(BookNotFoundError) as exc_info:
        await use_case.execute("0000000000000")

    assert exc_info.value.isbn == "0000000000000"