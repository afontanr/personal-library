import asyncio

import pytest

from personal_library.domain.model.collection_book import (
    CollectionBook,
    ReadingPeriod,
)
from personal_library.domain.model.saga import SagaMembership
from personal_library.infrastructure.adapters.db.sqlite_collection_repository import (
    SqliteCollectionRepository,
)

TEST_DB = ":memory:"


@pytest.mark.asyncio
async def test_save_and_find_by_isbn():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    book = CollectionBook(
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
        added_at="2026-05-15T16:00:00",
        reading_periods=[
            ReadingPeriod(start_date="2026-05-10", end_date="2026-05-15"),
        ],
    )

    await repo.save(book)

    found = await repo.find_by_isbn("9788466341172")
    assert found is not None
    assert found.isbn_13 == "9788466341172"
    assert found.isbn_10 == "846634117X"
    assert found.title == "Medio Mundo"
    assert found.authors == ["Joe Abercrombie"]
    assert found.description == "Una novela."
    assert found.published_date == "2026-05-19"
    assert found.cover_image_url == "https://example.com/cover.jpg"
    assert found.status == "new"
    assert found.rating == 4.0
    assert found.tags == ["fantasy"]
    assert found.opinion == "Buenisimo."
    assert found.added_at == "2026-05-15T16:00:00"
    assert len(found.reading_periods) == 1
    assert found.reading_periods[0].start_date == "2026-05-10"
    assert found.reading_periods[0].end_date == "2026-05-15"


@pytest.mark.asyncio
async def test_find_by_isbn_returns_none_for_missing():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    result = await repo.find_by_isbn("0000000000000")
    assert result is None


@pytest.mark.asyncio
async def test_find_all_returns_books_ordered_by_added_at_desc():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    book1 = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-10T10:00:00",
    )
    book2 = CollectionBook(
        isbn_13="9780451524935",
        title="1984",
        authors=["George Orwell"],
        added_at="2026-05-15T16:00:00",
    )

    await repo.save(book1)
    await repo.save(book2)

    books = await repo.find_all()
    assert len(books) == 2
    assert books[0].isbn_13 == "9780451524935"  # most recent first
    assert books[1].isbn_13 == "9788466341172"


@pytest.mark.asyncio
async def test_save_updates_existing_book():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    book = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-10T10:00:00",
        status="new",
        rating=None,
        tags=[],
    )
    await repo.save(book)

    updated = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-10T10:00:00",
        status="read",
        rating=4.5,
        tags=["fantasy"],
        opinion="Muy bueno.",
    )
    await repo.save(updated)

    found = await repo.find_by_isbn("9788466341172")
    assert found is not None
    assert found.status == "read"
    assert found.rating == 4.5
    assert found.tags == ["fantasy"]
    assert found.opinion == "Muy bueno."


@pytest.mark.asyncio
async def test_save_preserves_reading_periods_on_update():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    book = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-10T10:00:00",
        reading_periods=[
            ReadingPeriod(start_date="2026-01-01", end_date="2026-01-15"),
        ],
    )
    await repo.save(book)

    updated = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-10T10:00:00",
        reading_periods=[
            ReadingPeriod(start_date="2026-02-01", end_date="2026-02-20"),
            ReadingPeriod(start_date="2026-03-01", end_date=None),
        ],
    )
    await repo.save(updated)

    found = await repo.find_by_isbn("9788466341172")
    assert found is not None
    assert len(found.reading_periods) == 2
    assert found.reading_periods[0].start_date == "2026-02-01"
    assert found.reading_periods[1].start_date == "2026-03-01"


@pytest.mark.asyncio
async def test_find_all_returns_empty_list_when_no_books():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    books = await repo.find_all()
    assert books == []


@pytest.mark.asyncio
async def test_save_with_nullable_fields():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    book = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-15T16:00:00",
        isbn_10=None,
        description=None,
        published_date=None,
        cover_image_url=None,
        rating=None,
        opinion=None,
    )
    await repo.save(book)

    found = await repo.find_by_isbn("9788466341172")
    assert found is not None
    assert found.isbn_10 is None
    assert found.description is None
    assert found.published_date is None
    assert found.cover_image_url is None
    assert found.rating is None
    assert found.opinion is None


@pytest.mark.asyncio
async def test_save_rolls_back_on_reading_period_error():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    book = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-15T16:00:00",
    )
    await repo.save(book)

    bad_book = CollectionBook(
        isbn_13="9788466341172",
        title="After Crash",
        authors=["X"],
        added_at="2026-05-16T00:00:00",
        reading_periods=[
            ReadingPeriod(start_date=None, end_date=None),
        ],
    )

    original_commit = repo._db.commit
    call_count = [0]

    async def failing_commit():
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("simulated crash")

    repo._db.commit = failing_commit

    with pytest.raises(RuntimeError, match="simulated crash"):
        await repo.save(bad_book)

    repo._db.commit = original_commit

    found = await repo.find_by_isbn("9788466341172")
    assert found is not None
    assert found.title == "Medio Mundo"


@pytest.mark.asyncio
async def test_delete_removes_book_and_reading_periods():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    book = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-15T16:00:00",
        reading_periods=[
            ReadingPeriod(start_date="2026-05-10", end_date="2026-05-15"),
        ],
    )
    await repo.save(book)

    await repo.delete("9788466341172")

    found = await repo.find_by_isbn("9788466341172")
    assert found is None

    cursor = await repo._db.execute(
        "SELECT COUNT(*) FROM reading_periods WHERE isbn_13 = ?",
        ("9788466341172",),
    )
    count = (await cursor.fetchone())[0]
    assert count == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_book_does_not_raise():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    await repo.delete("0000000000000")

    books = await repo.find_all()
    assert books == []


@pytest.mark.asyncio
async def test_delete_only_removes_target_book():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    book1 = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-15T16:00:00",
    )
    book2 = CollectionBook(
        isbn_13="9780451524935",
        title="1984",
        authors=["George Orwell"],
        added_at="2026-05-10T10:00:00",
    )
    await repo.save(book1)
    await repo.save(book2)

    await repo.delete("9788466341172")

    remaining = await repo.find_all()
    assert len(remaining) == 1
    assert remaining[0].isbn_13 == "9780451524935"


@pytest.mark.asyncio
async def test_save_updates_added_at():
    repo = SqliteCollectionRepository(database_path=TEST_DB)
    await repo.initialize()

    def book(added_at: str) -> CollectionBook:
        return CollectionBook(
            isbn_13="9788466341172",
            title="Medio Mundo",
            authors=["Joe Abercrombie"],
            added_at=added_at,
        )

    try:
        await repo.save(book("2026-05-10T10:00:00"))
        await repo.save(book("2026-11-12T10:00:00"))

        found = await repo.find_by_isbn("9788466341172")
        assert found is not None
        assert found.added_at == "2026-11-12T10:00:00"
    finally:
        await repo.close()


# ─── Sagas ───


def _book(isbn_13: str, saga: SagaMembership | None = None) -> CollectionBook:
    return CollectionBook(
        isbn_13=isbn_13,
        title=f"Libro {isbn_13}",
        authors=["Autor"],
        added_at="2026-11-12T10:00:00",
        saga=saga,
    )


@pytest.fixture
async def repo():
    repository = SqliteCollectionRepository(database_path=TEST_DB)
    await repository.initialize()
    yield repository
    await repository.close()


async def test_save_book_with_saga_round_trips(repo):
    await repo.save(
        _book("9780000000001", SagaMembership("El Señor de los Anillos", 2))
    )
    found = await repo.find_by_isbn("9780000000001")
    assert found.saga.name == "El Señor de los Anillos"
    assert found.saga.volume == 2
    assert isinstance(found.saga.saga_id, int)


async def test_book_without_saga_reads_none(repo):
    await repo.save(_book("9780000000001"))
    assert (await repo.find_by_isbn("9780000000001")).saga is None


async def test_same_normalized_name_reuses_saga_and_keeps_first_spelling(repo):
    await repo.save(
        _book("9780000000001", SagaMembership("El Señor de los Anillos", 1))
    )
    await repo.save(
        _book("9780000000002", SagaMembership("  el senor de los ANILLOS ", 2))
    )
    sagas = await repo.find_all_sagas()
    assert [s.name for s in sagas] == ["El Señor de los Anillos"]
    second = await repo.find_by_isbn("9780000000002")
    assert second.saga.name == "El Señor de los Anillos"
    assert second.saga.saga_id == sagas[0].id


async def test_find_all_includes_saga(repo):
    await repo.save(_book("9780000000001", SagaMembership("Dune", 0)))
    [book] = await repo.find_all()
    assert book.saga.name == "Dune"
    assert book.saga.volume == 0


async def test_changing_saga_removes_orphan(repo):
    await repo.save(_book("9780000000001", SagaMembership("A")))
    await repo.save(_book("9780000000001", SagaMembership("B")))
    assert [s.name for s in await repo.find_all_sagas()] == ["B"]


async def test_removing_saga_from_book_removes_orphan(repo):
    await repo.save(_book("9780000000001", SagaMembership("A")))
    await repo.save(_book("9780000000001"))
    assert await repo.find_all_sagas() == []


async def test_deleting_books_keeps_saga_until_last_one(repo):
    await repo.save(_book("9780000000001", SagaMembership("A", 1)))
    await repo.save(_book("9780000000002", SagaMembership("A", 2)))
    await repo.delete("9780000000001")
    assert [s.name for s in await repo.find_all_sagas()] == ["A"]
    await repo.delete("9780000000002")
    assert await repo.find_all_sagas() == []


async def test_find_all_sagas_sorted_ignoring_case_and_accents(repo):
    for i, name in enumerate(["zeta", "Él", "alfa"], start=1):
        await repo.save(_book(f"978000000000{i}", SagaMembership(name)))
    assert [s.name for s in await repo.find_all_sagas()] == ["alfa", "Él", "zeta"]


async def test_concurrent_writes_do_not_abort_each_other(repo):
    await repo.save(_book("9780000000001", SagaMembership("A")))

    await asyncio.gather(
        repo.save(_book("9780000000002", SagaMembership("B"))),
        repo.delete("9780000000001"),
        repo.save(_book("9780000000003", SagaMembership("C"))),
    )

    assert await repo.find_by_isbn("9780000000001") is None
    assert [s.name for s in await repo.find_all_sagas()] == ["B", "C"]
