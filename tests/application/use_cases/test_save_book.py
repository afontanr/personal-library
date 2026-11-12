import dataclasses
from datetime import UTC, datetime

import pytest

from personal_library.application.use_cases.save_book import (
    SaveBookInput,
    SaveBookToCollection,
)
from personal_library.domain.model.collection_book import (
    CollectionBook,
)
from personal_library.domain.model.saga import SagaMembership
from personal_library.domain.ports.collection_repository import CollectionRepository


class FakeCollectionRepository(CollectionRepository):
    def __init__(self, books: list[CollectionBook] | None = None):
        self._books: dict[str, CollectionBook] = {b.isbn_13: b for b in books or []}

    @property
    def saved(self) -> list[CollectionBook]:
        return list(self._books.values())

    async def save(self, book: CollectionBook) -> None:
        self._books[book.isbn_13] = book

    async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
        return self._books.get(isbn_13)

    async def find_all(self) -> list[CollectionBook]:
        return list(self._books.values())

    async def delete(self, isbn_13: str) -> None:
        self._books.pop(isbn_13, None)


OLD_ADDED_AT = "2020-01-01T00:00:00+00:00"
ISBN = "9788466341172"


def _existing(status: str) -> CollectionBook:
    return CollectionBook(
        isbn_13=ISBN,
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at=OLD_ADDED_AT,
        status=status,
    )


async def _resave(existing_status: str | None, new_status: str, tags=None):
    books = [_existing(existing_status)] if existing_status else []
    use_case = SaveBookToCollection(
        collection_repository=FakeCollectionRepository(books)
    )
    return await use_case.execute(
        SaveBookInput(
            isbn_13=ISBN,
            title="Medio Mundo",
            authors=["Joe Abercrombie"],
            status=new_status,
            tags=tags or [],
        )
    )


@pytest.mark.asyncio
async def test_save_book_persists_collection_book():
    repo = FakeCollectionRepository()
    use_case = SaveBookToCollection(collection_repository=repo)

    book_input = SaveBookInput(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description="Una novela.",
        published_date="2026-05-19",
        cover_image_url="https://example.com/cover.jpg",
        status="new",
        rating=4.0,
        tags=["fantasy"],
        opinion="Buenisimo.",
        reading_periods=[
            SaveBookInput.ReadingPeriodInput(
                start_date="2026-05-10",
                end_date="2026-05-15",
            ),
        ],
    )

    result = await use_case.execute(book_input)

    assert result.isbn_13 == "9788466341172"
    assert result.isbn_10 == "846634117X"
    assert result.title == "Medio Mundo"
    assert result.authors == ["Joe Abercrombie"]
    assert result.description == "Una novela."
    assert result.published_date == "2026-05-19"
    assert result.cover_image_url == "https://example.com/cover.jpg"
    assert result.status == "new"
    assert result.rating == 4.0
    assert result.tags == ["fantasy"]
    assert result.opinion == "Buenisimo."
    assert result.added_at is not None
    assert len(result.reading_periods) == 1
    assert result.reading_periods[0].start_date == "2026-05-10"
    assert result.reading_periods[0].end_date == "2026-05-15"

    assert len(repo.saved) == 1
    assert repo.saved[0].isbn_13 == "9788466341172"


@pytest.mark.asyncio
async def test_save_book_sets_added_at_to_now():
    repo = FakeCollectionRepository()
    use_case = SaveBookToCollection(collection_repository=repo)

    before = datetime.now(UTC).isoformat()

    book_input = SaveBookInput(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
    )

    result = await use_case.execute(book_input)

    assert result.added_at >= before


@pytest.mark.asyncio
async def test_save_book_defaults_empty_fields():
    repo = FakeCollectionRepository()
    use_case = SaveBookToCollection(collection_repository=repo)

    book_input = SaveBookInput(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
    )

    result = await use_case.execute(book_input)

    assert result.status == "new"
    assert result.rating is None
    assert result.tags == []
    assert result.opinion is None
    assert result.reading_periods == []
    assert result.isbn_10 is None
    assert result.description is None
    assert result.published_date is None
    assert result.cover_image_url is None


async def test_resave_collection_book_keeps_added_at():
    result = await _resave("read", "read", tags=["fantasy"])

    assert result.added_at == OLD_ADDED_AT
    assert result.tags == ["fantasy"]


async def test_resave_to_buy_book_keeps_added_at():
    result = await _resave("to_buy", "to_buy")

    assert result.added_at == OLD_ADDED_AT
    assert result.status == "to_buy"


async def test_purchase_resets_added_at():
    before = datetime.now(UTC).isoformat()

    result = await _resave("to_buy", "new")

    assert result.added_at >= before


async def test_moving_collection_book_to_to_buy_keeps_added_at():
    result = await _resave("new", "to_buy")

    assert result.added_at == OLD_ADDED_AT


async def test_new_to_buy_book_gets_now():
    before = datetime.now(UTC).isoformat()

    result = await _resave(None, "to_buy")

    assert result.added_at >= before
    assert result.status == "to_buy"


def _input(saga: SaveBookInput.SagaInput | None = None) -> SaveBookInput:
    return SaveBookInput(isbn_13="9780000000001", title="T", authors=["A"], saga=saga)


async def test_save_book_with_saga_builds_membership():
    repo = FakeCollectionRepository()
    use_case = SaveBookToCollection(collection_repository=repo)

    result = await use_case.execute(
        _input(SaveBookInput.SagaInput(name="Dune", volume=1))
    )

    assert repo.saved[-1].saga == SagaMembership(name="Dune", volume=1)
    assert result.saga.name == "Dune"


async def test_save_book_returns_persisted_book():
    class CanonicalizingRepository(FakeCollectionRepository):
        async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
            book = await super().find_by_isbn(isbn_13)
            if book is None:
                return None
            return dataclasses.replace(
                book,
                saga=SagaMembership(name="El Señor de los Anillos", saga_id=1),
            )

    use_case = SaveBookToCollection(collection_repository=CanonicalizingRepository())

    result = await use_case.execute(
        _input(SaveBookInput.SagaInput(name="el senor de los anillos"))
    )

    assert result.saga.name == "El Señor de los Anillos"
    assert result.saga.saga_id == 1


async def test_save_book_rejects_blank_saga_name():
    repo = FakeCollectionRepository()
    use_case = SaveBookToCollection(collection_repository=repo)

    with pytest.raises(ValueError):
        await use_case.execute(_input(SaveBookInput.SagaInput(name="  ")))
    assert repo.saved == []
