import pytest

from personal_library.domain.model.collection_book import (
    CollectionBook,
    ReadingPeriod,
)
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
